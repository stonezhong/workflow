from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import TaskDefDTO

class TaskDefDAO:

    # 获取一个TaskDefDTO
    def get(self, id:str, *, session: Session) -> TaskDefDTO|None:
        return  session.get(TaskDefDTO, id)

    # 通过name, version获取一个TaskDefDTO
    def get_by_name_and_vesion(self, name:str, version:str, *, session: Session) -> TaskDefDTO|None:
        return session.execute(
            select(TaskDefDTO)
            .where(TaskDefDTO.name == name)
            .where(TaskDefDTO.version == version)
        ).scalars().one_or_none()

    # 列出全部TaskDefDTO
    def list(self, *, session:Session) -> List[TaskDefDTO]:
        task_defs = session.execute(select(TaskDefDTO)).scalars().all()
        return task_defs

    # 保存或创建新的TaskDefDTO
    # 创建新的TaskDefDTO，其id必须是None
    def save(self, task_def:TaskDefDTO, *, session:Session) -> TaskDefDTO:
        session.add(task_def)
        session.flush()
        return task_def
