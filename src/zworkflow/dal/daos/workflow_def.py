from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import WorkflowDefDTO

class WorkflowDefDAO:

    # 获取一个WorkflowDefDTO
    def get(self, id:str, *, session: Session) -> WorkflowDefDTO|None:
        return session.get(WorkflowDefDTO, id)

    # 通过name, version获取一个WorkflowDefDTO
    def get_by_name_and_version(self, name:str, version:str, *, session: Session) -> WorkflowDefDTO|None:
        return session.execute(
            select(WorkflowDefDTO)
            .where(WorkflowDefDTO.name == name)
            .where(WorkflowDefDTO.version == version)
        ).scalars().one_or_none()

    # 列出全部WorkflowDefDTO
    def list(self, *, session:Session) -> List[WorkflowDefDTO]:
        workflow_defs = session.execute(select(WorkflowDefDTO)).scalars().all()
        return workflow_defs

    # 保存或创建新的WorkflowDefDTO
    # 创建新的WorkflowDefDTO，其id必须是None
    def save(self, workflow_def:WorkflowDefDTO, *, session:Session) -> WorkflowDefDTO:
        session.add(workflow_def)
        session.flush()
        return workflow_def
