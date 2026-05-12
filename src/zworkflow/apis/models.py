from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

from zworkflow.dal.dtos import StepDefType, WorkflowState, TaskState

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
    invoke_task_def: APITaskDef | None = None
    invoke_workflow_def: APIWorkflowDef | None = None

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
    invoke_task_def_nv:     APINameAndVersion | None = None
    invoke_workflow_def_nv: APINameAndVersion | None = None

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
    state: WorkflowState
    steps: List[APIStep] = Field(default_factory=list)

class APITask(BaseModel):
    id: str
    task_def: APITaskDef
    input: dict|None
    output: dict|None
    state: TaskState

class APIStep(BaseModel):
    id: str
    step_def: APIStepDef
    invoke_task: APITask|None
    invoke_workflow: APIWorkflow|None

class APICreateWorkflowDetails(BaseModel):
    workflow_def_nv: APINameAndVersion
    description: str
    title: str
    input: dict | None = None
