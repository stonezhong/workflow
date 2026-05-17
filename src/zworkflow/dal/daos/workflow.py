from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from typing import List

from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import WorkflowDTO, WorkflowState, TaskState, TaskDTO, StepDTO

class WorkflowDAO:

    # 获取一个WorkflowDTO
    def get(self, id:str, *, session: Session) -> WorkflowDTO|None:
        return  session.get(WorkflowDTO, id)

    # 列出全部WorkflowDTO
    def list(self, *, session:Session) -> List[WorkflowDTO]:
        workflows = session.execute(select(WorkflowDTO)).scalars().all()
        return workflows

    # 保存或创建新的WorkflowDTO
    # 创建新的WorkflowDTO，其id必须是None
    def save(self, workflow:WorkflowDTO, *, session:Session) -> WorkflowDTO:
        session.add(workflow)
        session.flush()
        return workflow
    
    # 将一个Workflow设置成RUN_REQUESTED状态
    def set_state_run_requested(self, id:str, *, session:Session):
        result = session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == id)
            .values(state=WorkflowState.RUN_REQUESTED)
        )
        session.flush()
        return result.rowcount > 0

    # 将一个Workflow设置成RUNNING状态
    def set_state_running(self, id:str, *, session:Session):
        result = session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == id)
            .values(
                state=WorkflowState.RUNNING,
                time_started=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    # 将一个Workflow设置成SUCCEEDED状态
    def set_state_succeeded(self, id:str, *, session:Session):
        result = session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == id)
            .values(
                state=WorkflowState.SUCCEEDED, 
                time_ended=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    # 将一个Workflow设置成FAILED状态
    def set_state_failed(self, id:str, *, session:Session):
        result = session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == id)
            .values(
                state=WorkflowState.FAILED,
                time_ended=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    # 设置一个workflow的output
    def set_output(self, workflow_id:str, output:dict|None, *, session:Session) -> None:
        session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == workflow_id)
            .values(output=output)
        )
        session.flush()

    # 将一个Task状态设置成RUNNING
    def set_task_state_running(self, task_id:str, *, session:Session) -> bool:
        result = session.execute(
            update(TaskDTO)
            .where(TaskDTO.id == task_id)
            .values(
                state=TaskState.RUNNING, 
                time_started=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    # put task in running state
    def set_task_state_failed(self, task_id:str, *, session:Session) -> bool:
        result = session.execute(
            update(TaskDTO)
            .where(TaskDTO.id == task_id)
            .values(
                state=TaskState.FAILED, 
                time_ended=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    def set_task_state_succeeded(self, task_id:str, output:dict, *, session:Session) -> bool:
        result = session.execute(
            update(TaskDTO)
            .where(TaskDTO.id == task_id)
            .values(
                state=TaskState.SUCCEEDED, 
                output=output, 
                time_ended=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        session.flush()
        return result.rowcount > 0

    def set_step_task(self, step_id:str, task_id:str, *, session:Session) -> bool:
        result = session.execute(
            update(StepDTO)
            .where(StepDTO.id == step_id)
            .values(invoke_task_id=task_id)
        )
        session.flush()
        return result.rowcount > 0

