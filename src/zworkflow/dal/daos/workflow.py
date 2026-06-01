from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from typing import List

from datetime import datetime, timezone
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
    
    def reset(self, workflow_dto:WorkflowDTO, *, session:Session)-> None:
        workflow_dto.state = WorkflowState.CREATED
        workflow_dto.output = None
        workflow_dto.time_started = None
        workflow_dto.time_ended = None
        session.flush()
        session.refresh(workflow_dto)
