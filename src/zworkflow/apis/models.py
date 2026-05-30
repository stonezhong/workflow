from __future__ import annotations

from typing import List
from datetime import datetime
import enum
from pydantic import BaseModel, Field

from zworkflow.dal.dtos import StepDefType, EventType

class APIWorkflowState(enum.Enum):
    CREATED     = "CREATED"
    SUBMITTED   = "SUBMITTED"
    RUNNING     = "RUNNING"
    SUCCEEDED   = "SUCCEEDED"
    FAILED      = "FAILED"

class APITaskState(enum.Enum):
    CREATED     = "CREATED"
    SUBMITTED   = "SUBMITTED"
    RUNNING     = "RUNNING"
    SUCCEEDED   = "SUCCEEDED"
    FAILED      = "FAILED"


class APIWorkflowDef(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    steps: List[APIStepDef]
    step_deps: List[APIStepDefDep]
    input_schema: dict|None = None
    output_schema: dict|None = None

class APIStepDef(BaseModel):
    id: str
    key: str
    description: str
    title: str
    type: StepDefType
    input: str                  # 表达式
    is_return_step: bool
    invoke_task_def: APITaskDef|None = None
    invoke_workflow_def: APIWorkflowDef|None = None

class APIStepDefDep(BaseModel):
    id: str
    source_step_def_key: str
    destination_step_def_key: str

class APITaskDef(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    input_schema: dict|None = None
    output_schema: dict|None = None

class APISchema(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    definition: dict

class APICreateSchemaDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    definition: dict

class APICreateTaskDefDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    input_schema: dict|None = None
    output_schema: dict|None = None

class APICreateWorkflowDefDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    steps: List[APICreateWorkflowDefStepDetails]
    step_deps: List[APIStepDefDepDetails]
    input_schema: dict|None = None
    output_schema: dict|None = None

class APICreateWorkflowDefStepDetails(BaseModel):
    key: str
    description: str
    title: str
    type: StepDefType
    input: str
    is_return_step: bool
    invoke_task_def_nv:     APINameAndVersion|None = None
    invoke_workflow_def_nv: APINameAndVersion|None = None

class APINameAndVersion(BaseModel):
    name: str
    version: str

class APIStepDefDepDetails(BaseModel):
    source_step_def_key: str
    destination_step_def_key: str

class APIWorkflow(BaseModel):
    id: str
    workflow_def: APIWorkflowDef
    description: str
    title: str
    input: dict | None = None
    output: dict | None = None
    state: APIWorkflowState
    steps: List[APIStep] = Field(default_factory=list)
    time_created: datetime
    time_started: datetime|None = None
    time_ended: datetime|None = None

class APITask(BaseModel):
    id: str
    task_def: APITaskDef
    input: dict|None=None
    output: dict|None=None
    state: APITaskState
    time_created: datetime
    time_started: datetime|None = None
    time_ended: datetime|None = None

class APIStep(BaseModel):
    id: str
    step_def: APIStepDef
    invoke_task: APITask|None = None
    invoke_workflow: APIWorkflow|None = None

class APICreateWorkflowDetails(BaseModel):
    workflow_def_nv: APINameAndVersion
    description: str
    title: str
    input: dict|None = None

class APIEvent(BaseModel):
    id: str
    event_time: datetime
    type: EventType
    workflow_id: str
    step_id: str|None
    task_id: str|None
    message: str
