from __future__ import annotations
from typing import List

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
    
    # 改变一个workflow的状态。源状态必须符合from_state
    def change_state(
            self, 
            id:str,
            from_state:WorkflowState, 
            to_state:WorkflowState, 
            *, 
            session:Session
    ) -> bool:
        result = session.execute(
            update(WorkflowDTO)
            .where(WorkflowDTO.id == id)
            .where(WorkflowDTO.state == from_state)
            .values(state=to_state)
        )
        session.flush()
        return result.rowcount > 0
    
    def set_task_state(self, task_id:str, state:TaskState, *, session:Session) -> bool:
        result = session.execute(
            update(TaskDTO)
            .where(TaskDTO.id == task_id)
            .values(state=state)
        )
        session.flush()
        return result.rowcount > 0

    def complete_task(self, task_id:str, output:dict, *, session:Session) -> bool:
        result = session.execute(
            update(TaskDTO)
            .where(TaskDTO.id == task_id)
            .values(state=TaskState.SUCCEEDED, output=output)
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

