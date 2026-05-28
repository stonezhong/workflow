from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import EventDTO

class EventDAO:

    # 获取一个EventDTO
    def get(self, id:str, *, session: Session) -> EventDTO|None:
        return  session.get(EventDTO, id)

    # 列出一个workflow的全部EventDTO
    def list(self, workflow_id:str, *, session:Session) -> List[EventDTO]:
        # TODO: get 子workflow的事件
        schemas = session.execute(
            select(EventDTO)
            .where(EventDTO.workflow_id == workflow_id)
            .order_by(EventDTO.event_time.asc())
        ).scalars().all()
        return schemas

    # 保存或创建新的SchemaDTO
    # 创建新的SchemaDTO，其id必须是None
    def save(self, event:EventDTO, *, session:Session) -> EventDTO:
        session.add(event)
        session.flush()
        return event
