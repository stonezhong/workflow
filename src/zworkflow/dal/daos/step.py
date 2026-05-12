from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import StepDTO

class StepDAO:

    # 获取一个StepDTO
    def get(self, id:str, *, session: Session) -> StepDTO|None:
        return  session.get(StepDTO, id)

    # 列出全部StepDTO
    def list(self, *, workflow_id: str, session:Session) -> List[StepDTO]:
        steps = session.execute(select(StepDTO).where(
            StepDTO.workflow_id == workflow_id
        )).scalars().all()
        return steps

    # 保存或创建新的StepDTO
    # 创建新的StepDTO，其id必须是None
    def save(self, step:StepDTO, *, session:Session) -> StepDTO:
        session.add(step)
        session.flush()
        return step
