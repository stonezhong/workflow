from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import StepDefDepDTO

class StepDefDepDAO:

    # StepDefDepDTO
    def get(self, id:str, *, session: Session) -> StepDefDepDTO|None:
        return  session.get(StepDefDepDTO, id)

    # 列出全部StepDefDepDTO
    def list(self, *, workflow_def_id: str, session:Session) -> List[StepDefDepDTO]:
        step_def_deps = session.execute(select(StepDefDepDTO).where(
            StepDefDepDTO.workflow_def_id == workflow_def_id
        )).scalars().all()
        return step_def_deps

    # 保存或创建新的StepDefDepDTO
    # 创建新的StepDefDepDTO，其id必须是None
    def save(self, step_def_dep:StepDefDepDTO, *, session:Session) -> StepDefDepDTO:
        session.add(step_def_dep)
        session.flush()
        return step_def_dep
