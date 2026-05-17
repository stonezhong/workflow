from __future__ import annotations

import logging.config
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from temporalio import activity

from zworkflow.app_config import app_config
from zworkflow.core.services import WorkflowService
from zworkflow.dal.dtos import StepDefType, TaskState

@activity.defn
async def greet(name: str) -> str:
    return f"Hello {name}"

from .task_map import ACTIVITY_HANDLER_MAP

@activity.defn
async def generic_activity(step_id: str) -> None:
    logger.info(f"generic_activity({step_id}): enter")

    # 加载任务参数
    workflow_service = WorkflowService()
    engine:Engine = create_engine(app_config.database.url, connect_args=app_config.database.connect_args)
    with Session(engine) as session:
        with session.begin() as transaction:
            zworkflow, step = workflow_service.get_step(step_id, session=session)
            logger.info(f"generic_activity({step_id}): step key = {step.step_def.key}, step type: {step.step_def.type}, workflow_id = {zworkflow.id}")

            if step.step_def.type != StepDefType.TASK:
                # 目前，activity只支持执行task。如果不是task，则立刻返回
                logger.warning(f"generic_activity({step_id}): type is {step.step_def.type},  not yet supported!")
                return None

            task = step.invoke_task
            if task is None:
                logger.warning(f"generic_activity({step_id}): task not found")
                return None

            task_def = step.step_def.invoke_task_def
            logger.info(f"generic_activity({step_id}): task id = {task.id}, task state = {task.state}, task name: {task_def.name}, task version: {task_def.version}, task input: {task.input}")
            
            ####################################################################
            # 进入这个函数的时候，task的状态应该是RUN_REQUESTED
            # 将task切换成RUNNING状态
            ####################################################################
            workflow_service.set_task_state_running(task.id, session=session)
            logger.info(f"generic_activity({step_id}): change task state to RUNNING")

    # 现在寻找handler，并且运行

    handler = ACTIVITY_HANDLER_MAP.get(task_def.name, {}).get(task_def.version)
    if handler is None:
        logger.info(f"generic_activity({step_id}): no handler, step failed")
        with Session(engine) as session:
            with session.begin() as transaction:
                workflow_service.set_task_state_failed(task.id, session=session)
        return None
    
    try:
        output = await handler(task.input)
        with Session(engine) as session:
            with session.begin() as transaction:
                workflow_service.set_task_state_succeeded(task.id, output, session=session)
                if step.step_def.is_return_step:
                    workflow_service.set_output(zworkflow.id, output, session=session)
                # TODO: save output
        logger.info(f"generic_activity({step_id}): task succeeded")
        return None
    except Exception as e:
        with Session(engine) as session:
            with session.begin() as transaction:
                workflow_service.set_task_state_failed(task.id, session=session)
        logger.error(f"generic_activity({step_id}): task failed", e)
        raise e



