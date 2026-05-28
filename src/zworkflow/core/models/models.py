from __future__ import annotations

from typing import List
from datetime import datetime
from pydantic import BaseModel, Field

from zworkflow.dal.dtos import StepDefType, WorkflowState, TaskState, EventType

######################################################################################
# 必须把这些model放在一个文件以避免循环索引
######################################################################################

class WorkflowDef(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    steps: List[StepDef]
    step_deps: List[StepDefDep]
    input_schema: dict|None = None
    output_schema: dict|None = None

class StepDef(BaseModel):
    id: str
    workflow_def: WorkflowDef
    key: str
    description: str
    title: str
    type: StepDefType
    input: str                  # 表达式
    is_return_step: bool
    invoke_task_def: TaskDef|None = None
    invoke_workflow_def: WorkflowDef|None = None

class StepDefDep(BaseModel):
    id: str
    workflow_def: WorkflowDef
    source_step_def_key: str
    destination_step_def_key: str

class TaskDef(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    input_schema: dict|None = None
    output_schema: dict|None = None

class Workflow(BaseModel):
    id: str
    workflow_def: WorkflowDef

    description: str
    title: str

    input: dict|None = None
    output: dict|None = None

    state: WorkflowState
    steps: List[Step] = Field(default_factory=list)

    time_created: datetime
    time_started: datetime|None = None
    time_ended: datetime|None = None

class Step(BaseModel):
    id: str
    step_def: StepDef
    invoke_task: Task|None = None
    invoke_workflow: Workflow|None = None


class Task(BaseModel):
    id: str
    task_def: TaskDef
    input: dict|None = None
    output: dict|None = None
    state: TaskState
    time_created: datetime
    time_started: datetime|None = None
    time_ended: datetime|None = None

class CreateWorkflowDefDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    steps: List[CreateWorkflowDefStepDetails]
    step_deps: List[StepDefDepDetails]
    input_schema: dict|None = None
    output_schema: dict|None = None

class CreateWorkflowDefStepDetails(BaseModel):
    key: str
    description: str
    title: str
    type: StepDefType
    input: str
    is_return_step: bool
    invoke_task_def_nv:     NameAndVersion|None = None
    invoke_workflow_def_nv: NameAndVersion|None = None

class NameAndVersion(BaseModel):
    name: str
    version: str

class StepDefDepDetails(BaseModel):
    source_step_def_key: str
    destination_step_def_key: str

class CreateTaskDefDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    input_schema: dict|None = None
    output_schema: dict|None = None

class CreateWorkflowDetails(BaseModel):
    parent_id: str|None = None
    workflow_def_nv: NameAndVersion
    description: str
    title: str
    input: dict|None = None

class CreateSchemaDetails(BaseModel):
    name: str
    version: str
    description: str
    title: str
    definition: dict

class Schema(BaseModel):
    id: str
    name: str
    version: str
    description: str
    title: str
    definition: dict

class CreateEventDetails(BaseModel):
    workflow_id: str
    type: EventType
    message: str
    step_id: str|None = None
    task_id: str|None = None

class Event(BaseModel):
    id: str
    event_time: datetime
    type: EventType
    workflow_id: str
    message: str
    step_id: str|None = None
    task_id: str|None = None
