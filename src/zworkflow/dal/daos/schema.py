from __future__ import annotations
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import SchemaDTO

class SchemaDAO:

    # 获取一个SchemaDTO
    def get(self, id:str, *, session: Session) -> SchemaDTO|None:
        return  session.get(SchemaDTO, id)

    # 列出全部SchemaDTO
    def list(self, *, session:Session) -> List[SchemaDTO]:
        schemas = session.execute(select(SchemaDTO)).scalars().all()
        return schemas

    # 保存或创建新的SchemaDTO
    # 创建新的SchemaDTO，其id必须是None
    def save(self, schema:SchemaDTO, *, session:Session) -> SchemaDTO:
        session.add(schema)
        session.flush()
        return schema
