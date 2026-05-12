from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import TaskDTO

class TaskDAO:

    # 获取一个TaskDTO
    def get(self, id:str, *, session: Session) -> TaskDTO|None:
        return  session.get(TaskDTO, id)

    # 列出全部TaskDTO
    def list(self, *, workflow_id: str, session:Session) -> List[TaskDTO]:
        tasks = session.execute(select(TaskDTO).where(
            TaskDTO.workflow_id == workflow_id
        )).scalars().all()
        return tasks

    # 保存或创建新的TaskDTO
    # 创建新的TaskDTO，其id必须是None
    def save(self, task:TaskDTO, *, session:Session) -> TaskDTO:
        session.add(task)
        session.flush()
        return task
