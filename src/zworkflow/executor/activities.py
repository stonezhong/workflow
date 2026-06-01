from __future__ import annotations

import logging.config
import logging
logger = logging.getLogger(__name__)

import traceback
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from temporalio import activity
import contextlib

from zworkflow.app_config import app_config
from zworkflow.core.services import WorkflowService, EventService
from zworkflow.core.models import CreateEventDetails
from zworkflow.dal.dtos import StepDefType, TaskState, EventType

@activity.defn
async def greet(name: str) -> str:
    return f"Hello {name}"

from .task_map import ACTIVITY_HANDLER_MAP

@activity.defn
async def generic_activity(step_id: str) -> None:
    logger.info(f"generic_activity({step_id}): enter")

    # 加载任务参数
    workflow_service = WorkflowService()
    event_service = EventService()

    engine:Engine = create_engine(app_config.database.url, connect_args=app_config.database.connect_args)

    # 等待20秒，让task进入RUN_REQUESTED状态
    # 如果等待超时，不要扔出异常，悄悄地退出，将来可以重新执行这些workflow
    if not await workflow_service.wait_for_task_in_run_requested_state(step_id, 20, engine=engine):
        logger.info(f"generic_activity({step_id}): task is not in RUN_REQUESTED state after waiting for 20 seconds")
        return


    def log_task_output(task_id:str, message:str)-> None:
        with Session(engine) as session:
            with session.begin() as transaction:
                event_service.create(
                    CreateEventDetails(
                        type = EventType.TASK_OUTPUT,
                        workflow_id = zworkflow.id,
                        step_id = step_id,
                        task_id = task_id,
                        message = message
                    ),
                    session=session
                )


    with Session(engine) as session:
        with session.begin():
            zworkflow, step = workflow_service.get_step(step_id, session=session)
            logger.info(f"generic_activity({step_id}): step key = {step.step_def.key}, step type: {step.step_def.type}, workflow_id = {zworkflow.id}")
            assert step.step_def.type == StepDefType.TASK
            assert step.invoke_task is not None
            task = step.invoke_task
            task_def = step.step_def.invoke_task_def
            logger.info(f"generic_activity({step_id}): task id = {task.id}, task state = {task.state}, task name: {task_def.name}, task version: {task_def.version}, task input: {task.input}")
            
            # 需要改变task状态: RUN_REQUESTED --> RUNNING
            workflow_service.set_step_state_running(step_id, session=session)
            logger.info(f"generic_activity({step_id}): change task state to RUNNING")
            event_service.create(
                CreateEventDetails(
                    type = EventType.TASK_EXECUTION_STARTED,
                    workflow_id = zworkflow.id,
                    step_id = step_id,
                    task_id = task.id,
                    message = f"Task is started"
                ),
                session=session
            )

    # 现在寻找handler，并且运行

    handler = ACTIVITY_HANDLER_MAP.get(task_def.name, {}).get(task_def.version)
    if handler is None:
        logger.info(f"generic_activity({step_id}): no handler, step failed")
        with Session(engine) as session:
            with session.begin():
                workflow_service.set_step_state_failed(step_id, session=session)
                event_service.create(
                    CreateEventDetails(
                        type = EventType.TASK_EXECUTION_FAILED,
                        workflow_id = zworkflow.id,
                        step_id = step_id,
                        task_id = task.id,
                        message = f"Task {task_def.name}:{task_def.version} does not have handler"
                    ),
                    session=session
                )
        return None
    
    # 现在，检查输入是否匹配input的JSON Schema
    if task_def.input_schema is not None:
        try:
            validate(
                instance = task.input,
                schema = task_def.input_schema
            )
        except ValidationError as e:
            logger.info(f"generic_activity({step_id}): task input violate task schema")
            with Session(engine) as session:
                with session.begin():
                    workflow_service.set_step_state_failed(step_id, session=session)
                    event_service.create(
                        CreateEventDetails(
                            type = EventType.TASK_EXECUTION_FAILED,
                            workflow_id = zworkflow.id,
                            step_id = step_id,
                            task_id = task.id,
                            message = f"Task input violated task schema: {e}"
                        ),
                        session=session
                    )
            return None
    
    try:
        output = await handler(task.input, logger=lambda message: log_task_output(task.id, message))
    except Exception as e:
        stack = "".join(traceback.format_exception(e))
        with Session(engine) as session:
            with session.begin():
                workflow_service.set_step_state_failed(step_id, session=session)
                event_service.create(
                    CreateEventDetails(
                        type = EventType.TASK_EXECUTION_FAILED,
                        workflow_id = zworkflow.id,
                        step_id = step_id,
                        task_id = task.id,
                        message = stack
                    ),
                    session=session
                )
        logger.error(f"generic_activity({step_id}): task failed", e)
        raise e
    
    # Validate output
    # 现在，检查task的输出是否匹配output的JSON Schema
    if task_def.output_schema is not None:
        try:
            validate(
                instance = output,
                schema = task_def.output_schema
            )
        except ValidationError as e:
            logger.info(f"generic_activity({step_id}): task output violate task schema")
            with Session(engine) as session:
                with session.begin():
                    workflow_service.set_step_state_failed(step_id, session=session)
                    event_service.create(
                        CreateEventDetails(
                            type = EventType.TASK_EXECUTION_FAILED,
                            workflow_id = zworkflow.id,
                            step_id = step_id,
                            task_id = task.id,
                            message = f"Task output violated task schema: {e}"
                        ),
                        session=session
                    )
            return None

    # task output没有问题，可以将这个task设置成成功了。
    with Session(engine) as session:
        with session.begin():
            workflow_service.set_task_state_succeeded(step_id, output, session=session)
            event_service.create(
                CreateEventDetails(
                    type = EventType.TASK_EXECUTION_SUCCEEDED,
                    workflow_id = zworkflow.id,
                    step_id = step_id,
                    task_id = task.id,
                    message = f"Task is succeeded"
                ),
                session=session
            )
    logger.info(f"generic_activity({step_id}): task succeeded")
    return None


