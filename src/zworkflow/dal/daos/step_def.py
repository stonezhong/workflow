from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import StepDefDTO

class StepDefDAO:

    # 获取一个StepDefDTO
    def get(self, id:str, *, session: Session) -> StepDefDTO|None:
        return  session.get(StepDefDTO, id)

    # 列出全部StepDefDTO
    def list(self, *, workflow_def_id: str, session:Session) -> List[StepDefDTO]:
        task_defs = session.execute(select(StepDefDTO).where(
            StepDefDTO.workflow_def_id == workflow_def_id
        )).scalars().all()
        return task_defs

    # 保存或创建新的TaskDefDTO
    # 创建新的TaskDefDTO，其id必须是None
    def save(self, step_def:StepDefDTO, *, session:Session) -> StepDefDTO:
        session.add(step_def)
        session.flush()
        return step_def
