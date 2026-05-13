from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from typing import Tuple
from cel_expr_python import cel
from copy import deepcopy
import uuid
from typing import List
from sqlalchemy.orm import Session
from temporalio.client import Client

from zworkflow.app_config import AppConfig
from zworkflow.core.models import Schema, WorkflowDef, TaskDef, StepDef, StepDefDep, CreateWorkflowDefDetails, \
    CreateTaskDefDetails, Workflow, CreateWorkflowDetails, CreateSchemaDetails, Step, Task
from zworkflow.core.exceptions import WorkflowDefNotFound, TaskDefNotFound, BadInput, WorkflowNotFound, SchemaNotFound, StepDefNotFound, TaskNotFound

from zworkflow.dal.dtos import SchemaDTO, TaskDefDTO, WorkflowDefDTO, StepDefDTO, StepDefDepDTO, WorkflowDTO, TaskDTO, StepDTO
from zworkflow.dal.dtos import StepDefType, WorkflowState, TaskState
from zworkflow.dal.daos import SchemaDAO, WorkflowDefDAO, StepDefDAO, StepDefDepDAO, TaskDefDAO, WorkflowDAO, TaskDAO, StepDAO

from zworkflow.app_config import app_config

############################################################
# 负责workflow和task的定义
############################################################
class WorkflowDefService:

    workflow_def_dao: WorkflowDefDAO
    step_def_dao: StepDefDAO
    step_def_dep_dao: StepDefDepDAO
    task_def_dao: TaskDefDAO
    mapper: Mapper

    def __init__(self):
        self.workflow_def_dao = WorkflowDefDAO()
        self.step_def_dao = StepDefDAO()
        self.step_def_dep_dao = StepDefDepDAO()
        self.task_def_dao = TaskDefDAO()
        self.mapper = Mapper()

    ############################################################
    # 列出全部Workflow定义
    ############################################################
    def list(self, *, session:Session) -> List[WorkflowDef]:
        return [
            self.mapper.workflow_def_to_model(workflow_def_dto) for workflow_def_dto in self.workflow_def_dao.list(session=session)
        ]

    ############################################################
    # 通过name, version来获得Workflow定义
    ############################################################
    def get_workflow_def_by_name_and_version(self, *, name:str, version:str, session:Session) -> WorkflowDef|None:
        return self.mapper.workflow_def_to_model(self.workflow_def_dao.get_by_name_and_version(name, version, session=session))

    ############################################################
    # 通过id来获得Workflow定义
    ############################################################
    def get_workflow_def(self, id:str, *, session: Session) -> WorkflowDef|None:
        return self.mapper.workflow_def_to_model(self.workflow_def_dao.get(id, session=session))
    
    ############################################################
    # 通过name, version来获得task定义
    ############################################################
    def get_task_def_by_name_and_version(self, name:str, version:str, *, session:Session) -> TaskDef|None:
        return self.mapper.task_def_to_model(self.task_def_dao.get_by_name_and_version(name, version, session=session))

    ############################################################
    # 列出全部task定义
    ############################################################
    def list_tasks(self, *, session:Session) -> List[TaskDef]:
        task_def_dtos = self.task_def_dao.list(session=session)
        return [
            self.mapper.task_def_to_model(task_def_dto) for task_def_dto in task_def_dtos
        ]

    ############################################################
    # 通过id来获得Task定义
    ############################################################
    def get_task_def(self, id:str, *, session: Session) -> TaskDef|None:
        return self.mapper.task_def_to_model(self.task_def_dao.get(id, session=session))

    ############################################################
    # 创建一个Task定义
    ############################################################
    def create_task_def(self, create_task_def_details:CreateTaskDefDetails, *, session:Session) -> WorkflowDef:
        task_def_dto = TaskDefDTO(
            name = create_task_def_details.name,
            version = create_task_def_details.version,
            description = create_task_def_details.description,
            title = create_task_def_details.title,
            input_schema = create_task_def_details.input_schema,
            output_schema = create_task_def_details.output_schema
        )
        task_def_dto = self.task_def_dao.save(task_def_dto, session=session)
        return self.mapper.task_def_to_model(task_def_dto)

    ############################################################
    # 创建一个Workflow定义
    # 可能扔出的异常
    #     BadInput
    ############################################################
    def create_workflow_def(self, create_workflow_def_details:CreateWorkflowDefDetails, *, session:Session) -> WorkflowDef:
        # validate create_workflow_def_details
        step_keys = [step.key for step in create_workflow_def_details.steps]
        step_key_set = set(step_keys)
        if len(step_key_set) != len(step_keys):
            raise BadInput("Duplicate steps found!")
        for step_dep in create_workflow_def_details.step_deps:
            if step_dep.source_step_def_key not in step_key_set:
                raise BadInput(f"step {step_dep.source_step_def_key} is not defined")
            if step_dep.destination_step_def_key not in step_key_set:
                raise BadInput(f"step {step_dep.destination_step_def_key} is not defined")
        # TODO: check cyclic dependency
        

        workflow_def_dto = WorkflowDefDTO(
            name = create_workflow_def_details.name,
            version = create_workflow_def_details.version,
            description = create_workflow_def_details.description,
            title = create_workflow_def_details.title,
            input_schema = create_workflow_def_details.input_schema,
            output_schema = create_workflow_def_details.output_schema
        )
        workflow_def_dto = self.workflow_def_dao.save(workflow_def_dto, session=session)

        for step in create_workflow_def_details.steps:
            invoke_task_def = None
            invoke_workflow_def = None

            if step.type == StepDefType.TASK:
                if step.invoke_task_def_nv is None:
                    raise BadInput(f"step {step.key}: Missing task def name and version")
                invoke_task_def = self.task_def_dao.get_by_name_and_vesion(
                    step.invoke_task_def_nv.name, 
                    step.invoke_task_def_nv.version, 
                    session=session
                )
                if invoke_task_def is None:
                    raise BadInput(f"step {step.key}: task def not found for {step.invoke_task_def_nv.name}:{step.invoke_task_def_nv.version}")
            if step.type == StepDefType.WORKFLOW:
                if step.invoke_workflow_def_nv is None:
                    raise BadInput(f"step {step.key}: Missing workflow def name and version")
                invoke_workflow_def = self.workflow_def_dao.get_by_name_and_version(
                    step.invoke_workflow_def_nv.name,
                    step.invoke_workflow_def_nv.version,
                    sesison=session
                )
                if invoke_workflow_def is None:
                    raise BadInput(f"step {step.key}: workflow def not found for {step.invoke_workflow_def_nv.name}:{step.invoke_workflow_def_nv.version}")
            step_def_dto = StepDefDTO(
                workflow_def_id = workflow_def_dto.id,
                key = step.key,
                title = step.title,
                description = step.description,
                input = step.input,
                type = step.type,
                invoke_task_def_id = None if invoke_task_def is None else invoke_task_def.id,
                invoke_workflow_def_id = None if invoke_workflow_def is None else invoke_workflow_def.id              
            )
            self.step_def_dao.save(step_def_dto, session=session)
        
        for step_def_dep in create_workflow_def_details.step_deps:
            step_def_dep_dto = StepDefDepDTO(
                workflow_def_id = workflow_def_dto.id,
                source_step_def_key=step_def_dep.source_step_def_key,
                destination_step_def_key=step_def_dep.destination_step_def_key
            )
            self.step_def_dep_dao.save(step_def_dep_dto, session=session)

        return self.mapper.workflow_def_to_model(workflow_def_dto)

class WorkflowService:
    workflow_def_service: WorkflowDefService
    workflow_def_dao: WorkflowDefDAO
    workflow_dao: WorkflowDAO
    task_dao: TaskDAO
    step_dao: StepDAO
    mapper: Mapper

    def __init__(self):
        self.workflow_def_service = WorkflowDefService()
        self.workflow_def_dao = WorkflowDefDAO()
        self.workflow_dao = WorkflowDAO()
        self.task_dao = TaskDAO()
        self.step_dao = StepDAO()
        self.mapper = Mapper()

    ############################################################
    # 列出全部Workflow
    ############################################################
    def list(self, *, session:Session) -> List[Workflow]:
        return [
            self.mapper.workflow_to_model(workflow_dto) for workflow_dto in self.workflow_dao.list(session=session)
        ]

    ############################################################
    # 启动一个Workflow
    # 可能扔出的异常
    #     BadInput
    #     WorkflowDefNotFound
    ############################################################
    async def create_workflow(self, create_workflow_details:CreateWorkflowDetails, *, session:Session) -> Workflow:
        logger.debug(f"start_workflow: entre, create_workflow_details={create_workflow_details}")
        temporal_workflow_id = str(uuid.uuid4())
        
        workflow:Workflow = self.create_workflow_in_db(create_workflow_details, session = session)
        self.set_state_run_requested(workflow.id, session=session)
        client = await Client.connect(f"{app_config.temporal.host}:{app_config.temporal.port}")
        await client.start_workflow(
            "GenericWorkflow",
            workflow.id,
            id=temporal_workflow_id,
            task_queue=app_config.temporal.queue_name,
        )
        logger.debug(f"WorkflowService.start_workflow: notified temporal to start workflow in queue {app_config.temporal.queue_name}, workflow id = {workflow.id}, temporal workflow id = {temporal_workflow_id}")
        return workflow

    ############################################################
    # 创建一个Workflow
    # 可能扔出的异常
    #     BadInput
    #     WorkflowDefNotFound
    ############################################################
    def create_workflow_in_db(self, create_workflow_details:CreateWorkflowDetails, *, session:Session) -> Workflow:
        logger.debug(f"create_workflow: entre, create_workflow_details={create_workflow_details}")

        workflow_def = self.workflow_def_service.get_workflow_def_by_name_and_version(
            name = create_workflow_details.workflow_def_nv.name,
            version = create_workflow_details.workflow_def_nv.version,
            session = session
        )

        if workflow_def is None:
            raise WorkflowDefNotFound(
                f"workflow definition not found, name=\"{create_workflow_details.workflow_def_nv.name}\", version=\"{create_workflow_details.workflow_def_nv.version}\""
            )

        workflow_dto = WorkflowDTO(
            workflow_def_id = workflow_def.id,
            description = create_workflow_details.description,
            title = create_workflow_details.title,
            state = WorkflowState.CREATED,
            input = create_workflow_details.input,
            output = None
        )
        workflow_dto = self.workflow_dao.save(workflow_dto, session=session)
        logger.debug(f"create_workflow: WorkflowDTO is created, id = {workflow_dto.id}")

        # 创建全部的步骤。这些步骤并不指向任何Task或Workflow。它们指向的Task或Workflow在Step被执行的时候才会创建。
        for step_def in workflow_dto.workflow_def.steps:
            self.step_dao.save(
                StepDTO(
                    workflow_id = workflow_dto.id,
                    step_def_id = step_def.id,
                    invoke_task_id = None,
                    invoke_workflow_id = None
                ),
                session = session
            )

        logger.debug(f"create_workflow: exit, workflow(id={workflow_dto.id}) is created")
        return self.mapper.workflow_to_model(workflow_dto)

    ############################################################
    # 将一个Workflow的状态设置成RUN_REQUESTED
    ############################################################
    def set_state_run_requested(self, workflow_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_state_run_requested(id, session=session)

    ############################################################
    # 将一个Workflow的状态设置成RUNNING
    ############################################################
    def set_state_running(self, workflow_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_state_running(id, session=session)

    ############################################################
    # 将一个Workflow的状态设置成SUCCEEDED
    ############################################################
    def set_state_succeeded(self, workflow_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_state_succeeded(id, session=session)

    ############################################################
    # 将一个Workflow的状态设置成FAILED
    ############################################################
    def set_state_failed(self, workflow_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_state_failed(id, session=session)

    ############################################################
    # 通过id来获得一个Workflow
    ############################################################
    def get_workflow(self, id:str, *, session:Session) -> Workflow|None:
        return self.mapper.workflow_to_model(self.workflow_dao.get(id, session=session))

    
    ############################################################
    # 通过id来获得一个Step
    ############################################################
    def get_step(self, id:str, *, session:Session) -> Tuple[Workflow|None, Step|None]:
        step_dto = self.step_dao.get(id, session=session)
        if step_dto is None:
            return (None, None)
        workflow = self.mapper.workflow_to_model(step_dto.workflow)
        step = self.mapper.step_to_model(workflow.workflow_def, step_dto)
        return (workflow, step)


    def set_task_state_running(self, task_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_task_state_running(task_id, session=session)

    def set_task_state_failed(self, task_id:str, *, session:Session) -> bool:
        return self.workflow_dao.set_task_state_failed(task_id, session=session)

    def set_task_state_succeeded(self, task_id:str, output:dict, *, session:Session) -> bool:
        return self.workflow_dao.set_task_state_succeeded(task_id, output, session=session)

    ############################################################
    # 为执行一个步骤作准备
    # - 解析步骤的输入参数
    # - 将步骤对应的任务设置成RUNNING
    # - 将步骤对应的任务的input设置成解析后的步骤的输入
    ############################################################
    def prepare_execute_step(self, workflow_id: str, step:Step, *, session:Session) -> None:
        logger.debug(f"WorkflowService.prepare_execute_step: enter, workflow_id={workflow_id}, step={step.id}, step_key={step.step_def.key}")
        workflow = self.get_workflow(workflow_id, session=session)

        # compute step contexts
        steps = {}
        for xstep in workflow.steps:
            if xstep.step_def.type == StepDefType.TASK and xstep.invoke_task is not None and xstep.invoke_task.state == TaskState.SUCCEEDED:
                steps[xstep.step_def.key] = {"output": xstep.invoke_task.output}
                continue
            if xstep.step_def.type == StepDefType.WORKFLOW and xstep.invoke_workflow is not None and xstep.invoke_workflow.state == WorkflowState.SUCCEEDED:
                steps[xstep.step_def.key] = {"output": xstep.invoke_workflow.output}
                continue

        # 准备这个任务的输入参数
        env = cel.NewEnv(variables={
            "workflow": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
            "steps": cel.Type.Map(cel.Type.STRING, cel.Type.DYN),
        })
        input_expr = env.compile(step.step_def.input)

        step_input = input_expr.eval(data={
            "workflow": {
                "input": workflow.input,
            },
            "steps": steps
        })
        step_input_value = cel_to_python(step_input.value())
        logger.debug(f"WorkflowService.prepare_execute_step: workflow_id={workflow_id}, step={step.id}, step_key={step.step_def.key}, step_input_value = {step_input_value}")

        if step.step_def.type == StepDefType.TASK:
            task_dto = self.task_dao.save(
                TaskDTO(
                    workflow_id = workflow.id,
                    task_def_id = step.step_def.invoke_task_def.id,
                    state = TaskState.RUN_REQUESTED,
                    input = step_input_value,
                    output = None
                ),
                session = session
            )
            logger.debug(f"WorkflowService.prepare_execute_step: workflow_id={workflow_id}, step={step.id}, step_key={step.step_def.key}, task({task_dto.id}) is created")
            self.workflow_dao.set_step_task(step.id, task_dto.id, session=session)
            # caller may need to reload step since it has been changed

        elif step.step_def.type == StepDefType.WORKFLOW:
            raise NotImplementedError()

        logger.debug(f"WorkflowService.prepare_execute_step: workflow_id={workflow_id}, step={step.id}, step_key={step.step_def.key}, exit")



class SchemaService:
    schema_dao: SchemaDAO
    mapper: Mapper

    def __init__(self):
        self.schema_dao = SchemaDAO()
        self.mapper = Mapper()

    ############################################################
    # 列出全部Schema
    ############################################################
    def list(self, *, session:Session) -> List[Schema]:
        return [
            self.mapper.schema_to_model(schema_dto) for schema_dto in self.schema_dao.list(session=session)
        ]

    ############################################################
    # 创建一个Schema
    ############################################################
    async def create(self, create_schema_details:CreateSchemaDetails, *, session:Session) -> Schema:
        schema_dto = SchemaDTO(
            name = create_schema_details.name,
            version = create_schema_details.version,
            description = create_schema_details.description,
            title = create_schema_details.title,
            definition = deepcopy(create_schema_details.definition)
        )
        schema_dto = self.schema_dao.save(schema_dto, session=session)
        return self.mapper.schema_to_model(schema_dto)

    ############################################################
    # 通过id来获得Schema
    # 可能扔出的异常
    #     SchemaNotFound
    ############################################################
    def get(self, id:str, *, session: Session) -> Schema:
        schema_dto = self.schema_dao.get(id, session=session)
        if schema_dto is None:
            raise SchemaNotFound()
        return self.mapper.schema_to_model(schema_dto)

class Mapper:
    # XXX_to_model: dto to core model

    def task_def_to_model(self, task_def_dto:TaskDefDTO|None) -> TaskDef|None:
        return None if task_def_dto is None else TaskDef(
            id = task_def_dto.id,
            name = task_def_dto.name,
            version = task_def_dto.version,
            description = task_def_dto.description,
            title = task_def_dto.title,
            input_schema = deepcopy(task_def_dto.input_schema),
            output_schema = deepcopy(task_def_dto.output_schema)
        )
    
    def workflow_def_to_model(self, workflow_def_dto:WorkflowDefDTO|None) -> WorkflowDef|None:
        if workflow_def_dto is None:
            return None
        workflow_def = WorkflowDef(
            id = workflow_def_dto.id,
            name = workflow_def_dto.name,
            version = workflow_def_dto.version,
            description = workflow_def_dto.description,
            title = workflow_def_dto.title,
            steps = [],
            step_deps = [],
            input_schema = deepcopy(workflow_def_dto.input_schema),
            output_schema = deepcopy(workflow_def_dto.output_schema)
        )
        
        workflow_def.steps = [
            self.step_def_to_model(
                workflow_def,
                step_dto
            ) for step_dto in workflow_def_dto.steps
        ]

        workflow_def.step_deps = [
            self.step_def_dep_to_model(
                workflow_def,
                step_dep_dto
            ) for step_dep_dto in workflow_def_dto.step_deps
        ]

        return workflow_def
    
    def step_def_to_model(self, workflow_def: WorkflowDef, step_def_dto:StepDefDTO) -> StepDef:
        return StepDef(
            id = step_def_dto.id,
            workflow_def = workflow_def,
            key = step_def_dto.key,
            description = step_def_dto.description,
            title = step_def_dto.title,
            type = step_def_dto.type,
            input = step_def_dto.input,
            invoke_task_def = self.task_def_to_model(step_def_dto.invoke_task_def),
            invoke_workflow_def = self.workflow_def_to_model(step_def_dto.invoke_workflow_def)
        )
    
    def step_def_dep_to_model(self, workflow_def: WorkflowDef, step_def_dep_dto: StepDefDepDTO) -> StepDefDep:
        return StepDefDep(
            id = step_def_dep_dto.id,
            workflow_def = workflow_def,
            source_step_def_key = step_def_dep_dto.source_step_def_key,
            destination_step_def_key = step_def_dep_dto.destination_step_def_key
        )

    def workflow_to_model(self, workflow_dto: WorkflowDTO|None) -> Workflow|None:
        if workflow_dto is None:
            return None
        workflow_def = self.workflow_def_to_model(workflow_dto.workflow_def)
        workflow:Workflow = Workflow(
            id = workflow_dto.id,
            workflow_def = workflow_def,
            description = workflow_dto.description,
            title = workflow_dto.title,
            input = workflow_dto.input,
            output = workflow_dto.output,
            state = workflow_dto.state
        )
        for step_dto in workflow_dto.steps:
            workflow.steps.append(self.step_to_model(workflow_def, step_dto))
        return workflow
    
    def schema_to_model(self, schema_dto:SchemaDTO|None) -> Schema|None:
        return None if schema_dto is None else Schema(
            id = schema_dto.id,
            name = schema_dto.name,
            version = schema_dto.version,
            description = schema_dto.description,
            title = schema_dto.title,
            definition = deepcopy(schema_dto.definition)
        )
    
    def task_def_to_model(self, task_def_dto:TaskDefDTO|None) -> TaskDef|None:
        return None if task_def_dto is None else TaskDef(
            id = task_def_dto.id,
            name = task_def_dto.name,
            version = task_def_dto.version,
            description = task_def_dto.description,
            title = task_def_dto.title,
            input_schema = task_def_dto.input_schema,
            output_schema = task_def_dto.output_schema
        )

    def task_to_model(self, task_dto:TaskDTO) -> Task:
        return Task(
            id = task_dto.id,
            task_def = self.task_def_to_model(task_dto.task_def),
            state = task_dto.state,
            input = task_dto.input,
            output = task_dto.output
        )
    
    def step_to_model(self, workflow_def:WorkflowDef, step_dto:StepDTO) -> Step:
        assert step_dto.workflow.workflow_def_id == workflow_def.id
        return Step(
            id=step_dto.id,
            step_def=self.step_def_to_model(workflow_def, step_dto.step_def),
            invoke_task=None if step_dto.invoke_task_id is None else self.task_to_model(step_dto.invoke_task),
            invoke_workflow=None if step_dto.invoke_workflow_id is None else self.workflow_to_model(step_dto.invoke_workflow)
        )


def cel_to_python(cel_value):
    if cel_value is None:
        return None
    if isinstance(cel_value, dict):
        return {k: cel_to_python(v) for k, v in cel_value.items()}
    if isinstance(cel_value, list):
        return [cel_to_python(item) for item in cel_value]
    return cel_value.value() if hasattr(cel_value, 'value') else cel_value
        
