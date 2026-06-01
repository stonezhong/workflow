from __future__ import annotations

from typing import Tuple, Optional

import logging.config
import logging
logger = logging.getLogger(__name__)

import asyncio
import uuid
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from .activities import generic_activity
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from zworkflow.core.services import WorkflowService, EventService
from zworkflow.core.models import CreateEventDetails
from zworkflow.dal.dtos import WorkflowState, StepDefType, TaskState, EventType
from zworkflow.app_config import app_config
from zworkflow.core.models import Workflow, Step


logging.config.dictConfig(app_config.logging)

############################################################
# 检查是否应该执行一个步骤
############################################################
def may_run_step(step:Step) -> bool:
    if step.step_def.type == StepDefType.TASK:
        return step.invoke_task is None
    if step.step_def.type == StepDefType.WORKFLOW:
        return step.invoke_workflow is None
    assert False

############################################################
# 检查一个步骤是否成功了。
############################################################
def is_step_in_succeeded_state(step:Step) -> bool:
    if step.step_def.type == StepDefType.TASK:
        return step.invoke_task is not None and step.invoke_task.state == TaskState.SUCCEEDED
    if step.step_def.type == StepDefType.WORKFLOW:
        return step.invoke_workflow is not None and step.invoke_workflow.state == WorkflowState.SUCCEEDED
    return False

############################################################
# 检查是否应该退出驱动workflow。
############################################################
def shall_quit_workflow_execution(zworkflow:Workflow) -> Tuple[bool, Optional[WorkflowState]]:
    has_failed_step = False
    for step in zworkflow.steps:
        if step.step_def.type == StepDefType.TASK:
            if step.invoke_task is None:
                continue
            if step.invoke_task.state not in (TaskState.SUCCEEDED, TaskState.FAILED):
                # 有任务还未完成，不要退出，继续等待
                return False, None
            if step.invoke_task.state == TaskState.FAILED:
                has_failed_step = True
            continue
        if step.step_def.type == StepDefType.WORKFLOW:
            if step.invoke_workflow is None:
                continue
            if step.invoke_workflow.state not in (WorkflowState.SUCCEEDED, WorkflowState.FAILED):
                # 有子workflow还未完成，不要退出，继续等待
                return False, None
            if step.invoke_workflow.state == WorkflowState.FAILED:
                has_failed_step = True
            continue
    return True, WorkflowState.FAILED if has_failed_step else WorkflowState.SUCCEEDED


############################################################
# 负责通用Workflow的执行
############################################################
@workflow.defn
class GenericWorkflow:

    @workflow.run
    async def run(self, workflow_input_tuple: Tuple[str, str|None]) -> None:
        ####################################################################
        # workflow_id总不是None
        # step_id: 对顶层workflow，它是None，否则，它是父workflow的一个step，不为None
        ####################################################################
        workflow_id, step_id = workflow_input_tuple

        ####################################################################
        # Temporal Worker会调用这个函数来执行一个 Workflow
        #
        # Temporal的workflow ID是随机产生的，workflow_id是zworkflow的workflow ID
        # 进入这个函数的时候，应该假设workflow的状态是RUN_REQUESTED
        ####################################################################
        logger.info(f"GenericWorkflow.run({workflow_id}): enter, step_id = {step_id}")

        event_service = EventService()

        temporal_workflow_id = workflow.info().workflow_id
        temporal_run_id      = workflow.info().run_id
        logger.info(f"GenericWorkflow.run({workflow_id}): temporal workflow id = {temporal_workflow_id}, temporal_run_id = {temporal_run_id}")

        workflow_service = WorkflowService()
        engine:Engine = create_engine(app_config.database.url, connect_args=app_config.database.connect_args)

        # 等待20秒，让workflow进入RUN_REQUESTED状态
        # 如果等待超时，不要扔出异常，悄悄地退出，将来可以重新执行这些workflow
        if not await workflow_service.wait_for_workflow_in_run_requested_state(workflow_id, 20, engine=engine):
            logger.info(f"GenericWorkflow.run({workflow_id}): workflow is not in RUN_REQUESTED state after waiting for 20 seconds")
            return

        # 需要改变workflow状态: RUN_REQUESTED --> RUNNING
        with Session(engine) as session:
            with session.begin():
                # 参数合法性检查
                if step_id is None:
                    reloaded_workflow = workflow_service.get_workflow(workflow_id, session=session)
                    assert reloaded_workflow is not None
                else:
                    reloaded_workflow, step = workflow_service.get_step(step_id, session=session)
                    assert reloaded_workflow is not None
                    assert step.invoke_workflow.id == workflow_id

                if step_id is None:
                    # 非nested workflow
                    workflow_service.set_state_running(workflow_id, session=session)
                else:
                    # nested workflow
                    workflow_service.set_step_state_running(step_id, session=session)
                event_service.create(
                    CreateEventDetails(
                        type = EventType.WORKFLOW_EXECUTION_STARTED,
                        workflow_id = workflow_id,
                        step_id = step_id,
                        task_id = None,
                        message = f"Workflow is started"
                    ),
                    session=session
                )

        # 持续驱动workflow
        while True:
            with Session(engine) as session:
                with session.begin():
                    reloaded_workflow = workflow_service.get_workflow(workflow_id, session=session)
                    assert reloaded_workflow is not None
                    logger.info(f"GenericWorkflow.run({workflow_id}): workflow is loaded from database")
            
            # 收集所有步骤的状态
            steps_by_key = {step.step_def.key : step for step in reloaded_workflow.steps}

            # 这些步骤是可能被运行的，但是还要检查依赖关系
            run_candidate_step_keys = set([step.step_def.key for step in reloaded_workflow.steps if may_run_step(step)])
            # 剔除由于依赖关系而无法执行的步骤
            for step_def in reloaded_workflow.workflow_def.step_deps:
                src_step_key = step_def.source_step_def_key
                dst_step_key = step_def.destination_step_def_key

                if dst_step_key not in run_candidate_step_keys:
                    continue

                src_step = steps_by_key[src_step_key]
                if not is_step_in_succeeded_state(src_step):
                    # source步骤还没完成，无法执行目标步骤
                    run_candidate_step_keys.remove(dst_step_key)
                    continue

                # TODO: 检查条件。如果有条件，即便src_step_key已经完成，也未必会执行目标步骤

            # 收集待运行步骤完成，查看run_candidate_step_keys
            logger.info(f"GenericWorkflow.run({workflow_id}): steps to run is collected: {list(run_candidate_step_keys)}")

            # 没有收集到可运行的步骤。
            if len(run_candidate_step_keys) == 0:
                shall_quit, next_workflow_state = shall_quit_workflow_execution(reloaded_workflow)
                if not shall_quit:
                    logger.info(f"GenericWorkflow.run({workflow_id}): workflow is not yet done.")
                    await asyncio.sleep(1)
                    # 等待5秒后重新检查workflow状态，注意，重新检查的时候，database session是新的。
                    continue

                logger.info(f"GenericWorkflow.run({workflow_id}): workflow worker decided to quit and set state to {next_workflow_state}")
                with Session(engine) as session:
                    with session.begin():
                        assert next_workflow_state in (WorkflowState.SUCCEEDED, WorkflowState.FAILED)
                        if next_workflow_state == WorkflowState.SUCCEEDED:
                            workflow_service.set_workflow_state_succeeded(step_id, reloaded_workflow.id, session=session)
                            logger.info(f"GenericWorkflow.run({workflow_id}): set state to SUCCEEDED")
                            event_service.create(
                                CreateEventDetails(
                                    type = EventType.WORKFLOW_EXECUTION_SUCCEEDED,
                                    workflow_id = workflow_id,
                                    step_id = step_id,
                                    task_id = None,
                                    message = f"Workflow is succeeded"
                                ),
                                session=session
                            )
                        if next_workflow_state == WorkflowState.FAILED:
                            workflow_service.set_workflow_state_failed(reloaded_workflow.id, session=session)
                            logger.info(f"GenericWorkflow.run({workflow_id}): set state to FAILED")
                            event_service.create(
                                CreateEventDetails(
                                    type = EventType.WORKFLOW_EXECUTION_FAILED,
                                    workflow_id = workflow_id,
                                    step_id = step_id,
                                    task_id = None,
                                    message = f"Workflow is failed"
                                ),
                                session=session
                            )
                break

            # 启动这些步骤
            with Session(engine) as session:
                with session.begin():
                    reloaded_workflow = workflow_service.get_workflow(workflow_id, session=session)
            for step_key in sorted(list(run_candidate_step_keys)):
                logger.info(f"GenericWorkflow.run({workflow_id}): execute step: {step_key}")
                step = steps_by_key[step_key]
                with Session(engine) as session:
                    with session.begin():
                        # 获取这个步骤的输入
                        step_input = workflow_service.resolve_step_input(reloaded_workflow, step)
                        # 创建相应的task或者子workflow
                        workflow_service.create_task_or_nested_workflow_for_step(step_input, reloaded_workflow, step, session=session)
                        _, step = workflow_service.get_step(step.id, session=session) 
                
                if step.step_def.type == StepDefType.TASK:
                    try:
                        # 递交temporal activity
                        workflow.start_activity(
                            generic_activity,
                            step.id,
                            schedule_to_close_timeout=timedelta(hours=1),
                            retry_policy=RetryPolicy(maximum_attempts=1),
                        )
                        logger.info(f"GenericWorkflow.run({workflow_id}): activity invoked successfully")
                        with Session(engine) as session:
                            with session.begin():
                                workflow_service.set_step_state_run_requested(step.id, session=session)
                                event_service.create(
                                    CreateEventDetails(
                                        type = EventType.TASK_SUBMITTED,
                                        workflow_id = workflow_id,
                                        step_id = step.id,
                                        task_id = step.invoke_task.id,
                                        message = f"Task is submitted"
                                    ),
                                    session=session
                                )
                    except Exception as e:
                        with Session(engine) as session:
                            with session.begin():
                                workflow_service.set_step_state_failed(step.id, session=session)
                                event_service.create(
                                    CreateEventDetails(
                                        type = EventType.TASK_EXECUTION_FAILED,
                                        workflow_id = workflow_id,
                                        step_id = step.id,
                                        task_id = step.invoke_task.id,
                                        message = f"Unable to invoke activity: {e}"
                                    ),
                                    session=session
                                )
                elif step.step_def.type == StepDefType.WORKFLOW:
                    try:
                        child_temporal_workflow_id = str(uuid.uuid4())
                        await workflow.start_child_workflow(
                            "GenericWorkflow",
                            (step.invoke_workflow.id, step.id),
                            id=child_temporal_workflow_id,
                            retry_policy=RetryPolicy(maximum_attempts=1)
                        )
                        logger.info(f"GenericWorkflow.run({workflow_id}): workflow invoked successfully")
                        with Session(engine) as session:
                            with session.begin():
                                workflow_service.set_step_state_run_requested(step.id, session=session)
                                event_service.create(
                                    CreateEventDetails(
                                        type = EventType.WORKFLOW_SUBMITTED,
                                        workflow_id = step.invoke_workflow.id,
                                        step_id = step.id,
                                        task_id = None,
                                        message = f"workflow is submitted"
                                    ),
                                    session=session
                                )
                    except Exception as e:
                        with Session(engine) as session:
                            with session.begin():
                                workflow_service.set_workflow_state_failed(step.invoke_workflow.id, session=session)
                                event_service.create(
                                    CreateEventDetails(
                                        type = EventType.WORKFLOW_EXECUTION_FAILED,
                                        workflow_id = step.invoke_workflow.id,
                                        step_id = step.id,
                                        task_id = None,
                                        message = f"Unable to invoke workflow: {e}"
                                    ),
                                    session=session
                                )
                    

        logger.info(f"GenericWorkflow.run({workflow_id}): exit")
        return
