from __future__ import annotations

from copy import deepcopy

from zworkflow.core.models import TaskDef, WorkflowDef, StepDef, StepDefDep, CreateTaskDefDetails, \
    NameAndVersion, CreateWorkflowDefStepDetails, CreateWorkflowDefDetails, StepDefDepDetails, Workflow, \
    CreateWorkflowDetails, Schema, CreateSchemaDetails, Step, Task
from .models  import APITaskDef, APIWorkflowDef, APIStepDef, APIStepDefDep, APICreateTaskDefDetails, APINameAndVersion, \
    APICreateWorkflowDefStepDetails, APICreateWorkflowDefDetails, APIStepDefDepDetails, APIWorkflow, APICreateWorkflowDetails, \
    APISchema, APICreateSchemaDetails, APIStep, APITask

class APIMapper:
    # XXX_to_api: 将domain model转换成API model

    def task_def_to_api(self, task_def:TaskDef|None) -> APITaskDef|None:
        return None if task_def is None else APITaskDef(
            id = task_def.id,
            name = task_def.name,
            version = task_def.version,
            description = task_def.description,
            title = task_def.title,
            input_schema = deepcopy(task_def.input_schema),
            output_schema = deepcopy(task_def.output_schema)
        )
    
    def workflow_def_to_api(self, workflow_def:WorkflowDef|None) -> APIWorkflowDef|None:
        return None if workflow_def is None else APIWorkflowDef(
            id = workflow_def.id,
            name = workflow_def.name,
            version = workflow_def.version,
            description = workflow_def.description,
            title = workflow_def.title,
            steps = [self.step_def_to_api(step) for step in workflow_def.steps],
            step_deps = [self.step_def_dep_to_api(step_dep) for step_dep in workflow_def.step_deps],
            input_schema = deepcopy(workflow_def.input_schema),
            output_schema = deepcopy(workflow_def.output_schema)
        )
    
    def step_def_to_api(self, step_dep:StepDef) -> APIStepDef:
        return APIStepDef(
            id = step_dep.id,
            key = step_dep.key,
            description = step_dep.description,
            title = step_dep.title,
            type = step_dep.type,
            input = step_dep.input,
            is_return_step = step_dep.is_return_step,
            invoke_task_def = self.task_def_to_api(step_dep.invoke_task_def),
            invoke_workflow_def = self.workflow_def_to_api(step_dep.invoke_workflow_def)
        )
    
    def step_def_dep_to_api(self, step_def_dep: StepDefDep) -> APIStepDefDep:
        return APIStepDefDep(
            id = step_def_dep.id,
            source_step_def_key = step_def_dep.source_step_def_key,
            destination_step_def_key = step_def_dep.destination_step_def_key
        )
    
    def workflow_to_api(self, workflow: Workflow|None) -> APIWorkflow|None:
        return None if workflow is None else APIWorkflow(
            id = workflow.id,
            workflow_def = self.workflow_def_to_api(workflow.workflow_def),
            description = workflow.description,
            title = workflow.title,
            input = workflow.input,
            output = workflow.output,
            state = workflow.state,
            steps = [self.step_to_api(step) for step in workflow.steps],
            time_created = workflow.time_created,
            time_started = workflow.time_started,
            time_ended = workflow.time_ended
        )
    
    def step_to_api(self, step:Step|None) -> APIStep|None:
        return None if step is None else APIStep(
            id = step.id,
            step_def = self.step_def_to_api(step.step_def),
            invoke_task = self.task_to_api(step.invoke_task),
            invoke_workflow = self.workflow_to_api(step.invoke_workflow)
        )

    def task_to_api(self, task:Task|None) -> APITask|None:
        return None if task is None else APITask(
            id = task.id,
            task_def = self.task_def_to_api(task.task_def),
            input = deepcopy(task.input),
            output = deepcopy(task.output),
            state = task.state,
            time_created = task.time_created,
            time_started = task.time_started,
            time_ended = task.time_ended
        )

    def schema_to_api(self, schema: Schema|None) -> APISchema|None:
        return None if schema is None else APISchema(
            id = schema.id,
            name = schema.name,
            version = schema.version,
            description = schema.description,
            title = schema.title,
            definition = deepcopy(schema.definition)
        )

    # XXX_to_model: 将API model转换成domain model

    def create_task_def_details_to_model(self, create_task_def_details:APICreateTaskDefDetails) -> CreateTaskDefDetails:
        return CreateTaskDefDetails(
            name = create_task_def_details.name,
            version = create_task_def_details.version,
            description = create_task_def_details.description,
            title = create_task_def_details.title,
            input_schema = deepcopy(create_task_def_details.input_schema),
            output_schema = deepcopy(create_task_def_details.output_schema)
        )
    
    def name_and_version_to_model(self, name_and_version:APINameAndVersion|None) -> NameAndVersion:
        return None if name_and_version is None else NameAndVersion(
            name = name_and_version.name,
            version = name_and_version.version
        )

    def create_workflow_def_step_details_to_model(self, create_workflow_def_step_details:APICreateWorkflowDefStepDetails) -> CreateWorkflowDefStepDetails:
        return CreateWorkflowDefStepDetails(
            key = create_workflow_def_step_details.key,
            description = create_workflow_def_step_details.description,
            title = create_workflow_def_step_details.title,
            type = create_workflow_def_step_details.type,
            input = create_workflow_def_step_details.input,
            is_return_step = create_workflow_def_step_details.is_return_step,
            invoke_task_def_nv = self.name_and_version_to_model(create_workflow_def_step_details.invoke_task_def_nv),
            invoke_workflow_def_nv = self.name_and_version_to_model(create_workflow_def_step_details.invoke_workflow_def_nv)
        )
    
    def step_def_dep_details_to_model(self, step_def_dep_details:APIStepDefDepDetails) -> StepDefDepDetails:
        return StepDefDepDetails(
            source_step_def_key = step_def_dep_details.source_step_def_key,
            destination_step_def_key = step_def_dep_details.destination_step_def_key
        )

    
    def create_workflow_def_details_to_model(self, create_workflow_def_details: APICreateWorkflowDefDetails) -> CreateWorkflowDefDetails:
        return CreateWorkflowDefDetails(
            name = create_workflow_def_details.name,
            version = create_workflow_def_details.version,
            description = create_workflow_def_details.description,
            title = create_workflow_def_details.title,
            steps = [self.create_workflow_def_step_details_to_model(step) for step in create_workflow_def_details.steps],
            step_deps = [self.step_def_dep_details_to_model(step_dep) for step_dep in create_workflow_def_details.step_deps],
            input_schema = deepcopy(create_workflow_def_details.input_schema),
            output_schema = deepcopy(create_workflow_def_details.output_schema)
        )
    
    def create_workflow_details_to_model(self, create_workflow_details: APICreateWorkflowDetails) -> CreateWorkflowDetails:
        return CreateWorkflowDetails(
            workflow_def_nv = NameAndVersion(
                name = create_workflow_details.workflow_def_nv.name,
                version = create_workflow_details.workflow_def_nv.version
            ),
            description = create_workflow_details.description,
            title = create_workflow_details.title,
            input = create_workflow_details.input
        )

    def create_schema_details_to_model(self, create_schema_details: APICreateSchemaDetails) -> CreateSchemaDetails:
        return CreateSchemaDetails(
            name = create_schema_details.name,
            version = create_schema_details.version,
            description = create_schema_details.description,
            title = create_schema_details.title,
            definition = deepcopy(create_schema_details.definition)
        )
