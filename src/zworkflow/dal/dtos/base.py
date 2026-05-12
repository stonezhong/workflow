from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase

class Base(MappedAsDataclass, DeclarativeBase):
    pass

def create_all_tables(engine:Engine):
    Base.metadata.create_all(engine)