from __future__ import annotations

from typing import Tuple, Optional

import logging.config
import logging
logger = logging.getLogger(__name__)

import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities import generic_activity
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from zworkflow.core.services import WorkflowService
from zworkflow.dal.dtos import WorkflowState, StepDefType, TaskState
from zworkflow.app_config import app_config
from zworkflow.core.models import Workflow, Step
from zworkflow.core.exceptions import WorkflowNotFound


logging.config.dictConfig(app_config.logging)

##################################################################################################################################
# TODO:
# 为了避免竞争，所有子workflow运行时，必须锁定顶层workflow
# 目前还不支持取消workflow
# 目前还不支持取消task
##################################################################################################################################


# 检查是否应该执行一个步骤
def may_run_step(step:Step) -> bool:
    if step.step_def.type == StepDefType.TASK:
        return step.invoke_task is None
    if step.step_def.type == StepDefType.WORKFLOW:
        return step.invoke_workflow is None
    assert False

# 检查一个步骤是否成功了。
def is_step_in_succeeded_state(step:Step) -> bool:
    if step.step_def.type == StepDefType.TASK:
        return step.invoke_task is not None and step.invoke_task.state == TaskState.SUCCEEDED
    if step.step_def.type == StepDefType.WORKFLOW:
        return step.invoke_workflow is not None and step.invoke_workflow.state == WorkflowState.SUCCEEDED
    assert False

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
    async def run(self, workflow_id: str) -> None:
        ####################################################################
        # Temporal Worker会调用这个函数来执行一个 Workflow
        #
        # Temporal的workflow ID是随机产生的，workflow_id是zworkflow的workflow ID
        # 进入这个函数的时候，应该假设workflow的状态是RUN_REQUESTED
        ####################################################################

        logger.info(f"GenericWorkflow.run({workflow_id}): enter")

        temporal_workflow_id = workflow.info().workflow_id
        temporal_run_id      = workflow.info().run_id
        logger.info(f"GenericWorkflow.run({workflow_id}): temporal workflow id = {temporal_workflow_id}, temporal_run_id = {temporal_run_id}")

        workflow_service = WorkflowService()
        engine:Engine = create_engine(app_config.database.url, connect_args=app_config.database.connect_args)

        # 需要改变workflow状态: RUN_REQUESTED --> RUNNING
        # 如果失败，则否则则拒绝执行，直接退出
        with Session(engine) as session:
            with session.begin() as transaction:
                zworkflow:Workflow = workflow_service.get_workflow(workflow_id, session=session)
                if zworkflow is None:
                    # workflow不存在，毋需继续
                    logger.info(f"GenericWorkflow.run({workflow_id}): exit, workflow does not exist")
                    return
                if not workflow_service.set_state_running(zworkflow.id, session=session):
                    # 无法切换成RUNNING状态，毋需继续
                    transaction.rollback() # 因为我们没有扔出异常，所以要主动rollback transaction
                    logger.info(f"GenericWorkflow.run({workflow_id}): exit, cannot change workflow state to running")
                    return
        
        # 持续驱动workflow
        while True:
            with Session(engine) as session:
                with session.begin() as transaction:
                    zworkflow:Workflow = workflow_service.get_workflow(workflow_id, session=session)
                    logger.info(f"GenericWorkflow.run({workflow_id}): workflow is loaded from database")
            
            # 收集所有步骤的状态
            steps_by_key = {step.step_def.key : step for step in zworkflow.steps}

            # 这些步骤是可能被运行的，但是还要检查依赖关系
            run_candidate_step_keys = set([step.step_def.key for step in zworkflow.steps if may_run_step(step)])
            # 剔除由于依赖关系而无法执行的步骤
            for step_def in zworkflow.workflow_def.step_deps:
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

            if len(run_candidate_step_keys) == 0:
                # 没有收集到可运行的步骤。
                shall_quit, next_workflow_state = shall_quit_workflow_execution(zworkflow)
                if not shall_quit:
                    logger.info(f"GenericWorkflow.run({workflow_id}): workflow is not yet done.")
                    await asyncio.sleep(5)
                    # 等待5秒后重新检查workflow状态，注意，重新检查的时候，database session是新的。
                    continue

                logger.info(f"GenericWorkflow.run({workflow_id}): workflow worker decided to quit and set state to {next_workflow_state}")
                with Session(engine) as session:
                    with session.begin() as transaction:
                        assert next_workflow_state in (WorkflowState.SUCCEEDED, WorkflowState.FAILED)
                        if next_workflow_state == WorkflowState.SUCCEEDED:
                            workflow_service.set_state_succeeded(zworkflow.id, session=session)
                            logger.info(f"GenericWorkflow.run({workflow_id}): set state to SUCCEEDED")
                        if next_workflow_state == WorkflowState.FAILED:
                            workflow_service.set_state_failed(zworkflow.id, session=session)
                            logger.info(f"GenericWorkflow.run({workflow_id}): set state to FAILED")
                break


            # 运行这些步骤
            # 需要同时运行多个步骤，而不是依次运行
            results = []
            for step_key in sorted(list(run_candidate_step_keys)):
                logger.info(f"GenericWorkflow.run({workflow_id}): execute step: {step_key}")
                step = steps_by_key[step_key]
                with Session(engine) as session:
                    with session.begin() as transaction:
                        workflow_service.prepare_execute_step(workflow_id, step, session=session)
                
                # try:
                results.append(workflow.execute_activity(
                    generic_activity,
                    step.id,
                    schedule_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                ))
                logger.info(f"GenericWorkflow.run({workflow_id}): activity invoked successfully")

                # except Exception as e:
                #     logger.exception(f"GenericWorkflow.run({workflow_id}): failed to call activity", e)
                #     # Workflow驱动器不要失败，但是最后会将workflow设置成失败状态退出
            
            returns = await asyncio.gather(*results, return_exceptions=True)
            # maybe log bit debug info here

        logger.info(f"GenericWorkflow.run({workflow_id}): exit")
        return
