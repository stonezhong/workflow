from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft202012Validator
import jsonschema
import asyncio
from typing import Tuple
from datetime import datetime, timezone, timedelta
from cel_expr_python import cel
from copy import deepcopy
import uuid
from typing import List
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from temporalio.client import Client
from temporalio.common import RetryPolicy

from zworkflow.app_config import AppConfig
from zworkflow.core.models import Schema, WorkflowDef, TaskDef, StepDef, StepDefDep, CreateWorkflowDefDetails, \
    CreateTaskDefDetails, Workflow, CreateWorkflowDetails, CreateSchemaDetails, Step, Task, NameAndVersion, Event, CreateEventDetails
from zworkflow.core.exceptions import WorkflowDefNotFound, BadInput, WorkflowNotFound, SchemaNotFound, \
    InvalidJSONSchema, FailedToSubmitWorkflow, WorkflowInputSchemaViolation

from zworkflow.dal.dtos import SchemaDTO, TaskDefDTO, WorkflowDefDTO, StepDefDTO, StepDefDepDTO, WorkflowDTO, TaskDTO, StepDTO, EventDTO, EventType
from zworkflow.dal.dtos import StepDefType, WorkflowState, TaskState
from zworkflow.dal.daos import SchemaDAO, WorkflowDefDAO, StepDefDAO, StepDefDepDAO, TaskDefDAO, WorkflowDAO, TaskDAO, StepDAO, EventDAO

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
    def get_by_name_and_version(self, *, name:str, version:str, session:Session) -> WorkflowDef|None:
        return self.mapper.workflow_def_to_model(self.workflow_def_dao.get_by_name_and_version(name, version, session=session))

    ############################################################
    # 通过id来获得Workflow定义
    ############################################################
    def get_workflow_def(self, id:str, *, session: Session) -> WorkflowDef|None:
        return self.mapper.workflow_def_to_model(self.workflow_def_dao.get(id, session=session))
    
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
    # 如果 create_task_def_details.input_schema 或 
    # create_task_def_details.output_schema不合法，则扔出异常
    # InvalidJSONSchema
    ############################################################
    def create_task_def(self, create_task_def_details:CreateTaskDefDetails, *, session:Session) -> TaskDef:
        if create_task_def_details.input_schema is not None:
            try:
                Draft202012Validator.check_schema(create_task_def_details.input_schema)
            except jsonschema.exceptions.SchemaError as e:
                raise InvalidJSONSchema(e.message) from e

        if create_task_def_details.output_schema is not None:
            try:
                Draft202012Validator.check_schema(create_task_def_details.output_schema)
            except jsonschema.exceptions.SchemaError as e:
                raise InvalidJSONSchema(e.message) from e

        task_def_dto = TaskDefDTO(
            name = create_task_def_details.name,
            version = create_task_def_details.version,
            description = create_task_def_details.description,
            title = create_task_def_details.title,
            input_schema = deepcopy(create_task_def_details.input_schema),
            output_schema = deepcopy(create_task_def_details.output_schema)
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

        # 这个检查必须在保存Workflow_def前做，否则如果workflow_def的name, version冲突，你得到的是其他类型的异常
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
                    session=session
                )
                if invoke_workflow_def is None:
                    raise BadInput(f"step {step.key}: workflow def not found for {step.invoke_workflow_def_nv.name}:{step.invoke_workflow_def_nv.version}")


        workflow_def_dto = WorkflowDefDTO(
            name = create_workflow_def_details.name,
            version = create_workflow_def_details.version,
            description = create_workflow_def_details.description,
            title = create_workflow_def_details.title,
            input_schema = deepcopy(create_workflow_def_details.input_schema),
            output_schema = deepcopy(create_workflow_def_details.output_schema)
        )
        workflow_def_dto = self.workflow_def_dao.save(workflow_def_dto, session=session)

        for step in create_workflow_def_details.steps:
            invoke_task_def = None
            invoke_workflow_def = None

            if step.type == StepDefType.TASK:
                assert step.invoke_task_def_nv is not None
                invoke_task_def = self.task_def_dao.get_by_name_and_vesion(
                    step.invoke_task_def_nv.name, 
                    step.invoke_task_def_nv.version, 
                    session=session
                )
                assert invoke_task_def is not None
            if step.type == StepDefType.WORKFLOW:
                assert step.invoke_workflow_def_nv is not None
                invoke_workflow_def = self.workflow_def_dao.get_by_name_and_version(
                    step.invoke_workflow_def_nv.name,
                    step.invoke_workflow_def_nv.version,
                    session=session
                )
                assert invoke_workflow_def is not None
            step_def_dto = StepDefDTO(
                workflow_def_id = workflow_def_dto.id,
                key = step.key,
                title = step.title,
                description = step.description,
                input = step.input,
                is_return_step = step.is_return_step,
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
    event_service: EventService
    workflow_def_dao: WorkflowDefDAO
    workflow_dao: WorkflowDAO
    task_dao: TaskDAO
    step_dao: StepDAO
    mapper: Mapper

    def __init__(self):
        self.workflow_def_service = WorkflowDefService()
        self.event_service = EventService()
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
    # 启动一个顶层的Workflow (而非nested workflow)
    # 可能扔出的异常
    #     BadInput
    #     WorkflowDefNotFound
    ############################################################
    async def create_workflow(self, create_workflow_details:CreateWorkflowDetails, *, session:Session) -> Workflow:
        logger.debug(f"start_workflow: entre, create_workflow_details={create_workflow_details}")
        temporal_workflow_id = str(uuid.uuid4())
        
        workflow_dto:WorkflowDTO = self._create_workflow_in_db(create_workflow_details, session = session)
        # 只启动，并不等待workflow结束
        # TODO: 捕捉temporal exception并且转化为WorkflowError
        client = await Client.connect(f"{app_config.temporal.host}:{app_config.temporal.port}")
        try:
            await client.start_workflow(
                "GenericWorkflow",
                (workflow_dto.id, None),
                id=temporal_workflow_id,
                task_queue=app_config.temporal.queue_name,
                retry_policy=RetryPolicy(maximum_attempts=1)
            )
            # workflow会等待知道状态切换成RUN_REQUESTED，参考generic_workflow.py
            self.set_state_run_requested(workflow_dto.id, session=session)
            self.event_service.create(
                CreateEventDetails(
                    type = EventType.WORKFLOW_SUBMITTED,
                    workflow_id = workflow_dto.id,
                    step_id = None,
                    task_id = None,
                    message = f"Workflow is submitted"
                ),
                session=session
            )

            logger.debug(f"WorkflowService.start_workflow: notified temporal to start workflow in queue {app_config.temporal.queue_name}, workflow id = {workflow_dto.id}, temporal workflow id = {temporal_workflow_id}")
            session.refresh(workflow_dto)
            return self.mapper.workflow_to_model(workflow_dto)
        except Exception as e:
            raise FailedToSubmitWorkflow(str(e)) from e



    ############################################################
    # 重试一个失败的Workflow
    # 可能扔出的异常
    #     BadInput
    #     WorkflowNotFound
    ############################################################
    async def restart_failed_workflow(self, workflow_id:str, *, session:Session) -> Workflow:
        logger.debug(f"restart_failed_workflow: entre, workflow_id={workflow_id}")

        workflow_dto = self.workflow_dao.get(workflow_id, session=session)
        if workflow_dto is None:
            logger.debug(f"restart_failed_workflow: exit, workflow(id={workflow_id}) does not exist")
            raise WorkflowNotFound

        if workflow_dto.state != WorkflowState.FAILED:
            logger.debug(f"restart_failed_workflow: exit, workflow(id={workflow_id}) is not failed")
            raise BadInput(f"restart_failed_workflow: exit, workflow(id={workflow_id}) is not failed")


        # 将Workflow状态恢复初值 (参考create_workflow_in_db)
        # 将全部失败的任务的状态设置成CREATED        
        for step_dto in workflow_dto.steps:
            if step_dto.step_def.type == StepDefType.TASK and step_dto.invoke_task is not None and step_dto.invoke_task.state == TaskState.FAILED:
                self.step_dao.reset(step_dto, session=session)
                logger.debug(f"restart_failed_workflow: workflow_id={workflow_id}, clear task for step(id={step_dto.id}, name={step_dto.step_def.key})")
                continue
            if step_dto.step_def.type == StepDefType.WORKFLOW and step_dto.invoke_workflow is not None and step_dto.invoke_workflow.state == WorkflowState.FAILED:
                self.step_dao.reset(step_dto, session=session)
                logger.debug(f"restart_failed_workflow: workflow_id={workflow_id}, clear task for step(id={step_dto.id}, name={step_dto.step_def.key})")
                continue
        
        self.workflow_dao.reset(workflow_dto, session=session)
        logger.debug(f"restart_failed_workflow: set workflow(workflow_id={workflow_id}) state to CREATED")

        client = await Client.connect(f"{app_config.temporal.host}:{app_config.temporal.port}")
        temporal_workflow_id = str(uuid.uuid4())
        # 只启动，并不等待workflow结束
        # TODO: 捕捉temporal exception并且转化为WorkflowError
        await client.start_workflow(
            "GenericWorkflow",
            (workflow_dto.id, None),
            id=temporal_workflow_id,
            task_queue=app_config.temporal.queue_name,
        )
        # workflow会等待知道状态切换成RUN_REQUESTED，参考generic_workflow.py
        self.set_state_run_requested(workflow_dto.id, session=session)
        self.event_service.create(
            CreateEventDetails(
                type = EventType.WORKFLOW_SUBMITTED,
                workflow_id = workflow_dto.id,
                step_id = None,
                task_id = None,
                message = f"Workflow is submitted"
            ),
            session=session
        )
        logger.debug(f"WorkflowService.restart_failed_workflow: notified temporal to start workflow in queue {app_config.temporal.queue_name}, workflow id = {workflow_dto.id}, temporal workflow id = {temporal_workflow_id}")
        logger.debug(f"restart_failed_workflow: exit")
        session.refresh(workflow_dto)
        return self.mapper.workflow_to_model(workflow_dto)

    ############################################################
    # 创建一个Workflow
    # - 创建WorkflowDTO
    # - 创建所有的StepDTO
    # 可能扔出的异常
    #     BadInput
    #     WorkflowDefNotFound
    ############################################################
    def _create_workflow_in_db(self, create_workflow_details:CreateWorkflowDetails, *, session:Session) -> WorkflowDTO:
        logger.debug(f"create_workflow: entre, _create_workflow_details={create_workflow_details}")

        workflow_def = self.workflow_def_service.get_by_name_and_version(
            name = create_workflow_details.workflow_def_nv.name,
            version = create_workflow_details.workflow_def_nv.version,
            session = session
        )

        if workflow_def is None:
            raise WorkflowDefNotFound(
                f"workflow definition not found, name=\"{create_workflow_details.workflow_def_nv.name}\", version=\"{create_workflow_details.workflow_def_nv.version}\""
            )

        # 如果需要，则检验输入是否符合schema
        if workflow_def.input_schema is not None:
            try:
                validate(
                    instance = create_workflow_details.input,
                    schema = workflow_def.input_schema
                )
            except ValidationError as e:
                logger.exception(f"create_workflow: input does not match schema")
                raise WorkflowInputSchemaViolation(str(e)) from e

        workflow_dto = WorkflowDTO(
            parent_id=create_workflow_details.parent_id,
            workflow_def_id = workflow_def.id,
            description = create_workflow_details.description,
            title = create_workflow_details.title,
            state = WorkflowState.CREATED,
            input = deepcopy(create_workflow_details.input),
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
        return workflow_dto

    ############################################################
    # 将一个步骤设置成RUN_REQUESTED
    # 并将这个步骤对应的task或nested workflow的状态一起更新
    ############################################################
    def set_step_state_run_requested(self, step_id: str, *, session:Session) -> None:
        step_dto = self.step_dao.get(step_id, session=session)
        if step_dto.step_def.type == StepDefType.TASK:
            step_dto.invoke_task.state = TaskState.RUN_REQUESTED
            step_dto.invoke_task.output = None
            step_dto.invoke_task.time_started = None
            step_dto.invoke_task.time_ended = None
        elif step_dto.step_def.type == StepDefType.WORKFLOW:
            step_dto.invoke_workflow.state = WorkflowState.RUN_REQUESTED
            step_dto.invoke_workflow.output = None
            step_dto.invoke_workflow.time_started = None
            step_dto.invoke_workflow.time_ended = None
        session.flush()

    ############################################################
    # 将一个Workflow的状态设置成RUN_REQUESTED
    ############################################################
    def set_state_run_requested(self, workflow_id:str, *, session:Session) -> None:
        workflow_dto = self.workflow_dao.get(workflow_id, session=session)
        workflow_dto.state = WorkflowState.RUN_REQUESTED
        workflow_dto.output = None
        workflow_dto.time_started = None
        workflow_dto.time_ended = None
        session.flush()

    ############################################################
    # 将一个步骤的状态设置成RUNNING
    # 并将这个步骤对应的task或nested workflow的状态一起更新
    ############################################################
    def set_step_state_running(self, step_id:str, *, session:Session) -> None:
        time_started = datetime.now(timezone.utc).replace(tzinfo=None)
        step_dto = self.step_dao.get(step_id, session=session)
        if step_dto.step_def.type == StepDefType.TASK:
            step_dto.invoke_task.state = TaskState.RUNNING
            step_dto.invoke_task.output = None
            step_dto.invoke_task.time_started = time_started
            step_dto.invoke_task.time_ended = None
        elif step_dto.step_def.type == StepDefType.WORKFLOW:
            step_dto.invoke_workflow.state = WorkflowState.RUNNING
            step_dto.invoke_workflow.output = None
            step_dto.invoke_workflow.time_started = time_started
            step_dto.invoke_workflow.time_ended = None
        session.flush()

    ############################################################
    # 将一个Workflow的状态设置成RUNNING
    ############################################################
    def set_state_running(self, workflow_id:str, *, session:Session) -> None:
        workflow_dto = self.workflow_dao.get(workflow_id, session=session)
        workflow_dto.state = WorkflowState.RUNNING
        workflow_dto.output = None
        workflow_dto.time_started = datetime.now(timezone.utc).replace(tzinfo=None)
        workflow_dto.time_ended = None
        session.flush()

    ############################################################
    # 将一个步骤的状态设置成SUCCEEDED
    # 并将这个步骤对应的task或nested workflow的状态一起更新
    ############################################################
    def set_task_state_succeeded(self, step_id:str, output:dict|None, *, session:Session) -> None:
        time_ended = datetime.now(timezone.utc).replace(tzinfo=None)
        step_dto = self.step_dao.get(step_id, session=session)
        assert step_dto.step_def.type == StepDefType.TASK
        assert step_dto.invoke_task is not None

        step_dto.invoke_task.state = TaskState.SUCCEEDED
        step_dto.invoke_task.time_ended = time_ended
        step_dto.invoke_task.output = deepcopy(output)
        
        if step_dto.step_def.is_return_step:
            step_dto.workflow.output = deepcopy(output)
        session.flush()

    ############################################################
    # 将一个Workflow的状态设置成SUCCEEDED
    # 如果这个workflow从属于一个step，则视情况progate workflow output到父workflow
    ############################################################
    def set_workflow_state_succeeded(self, step_id:str, workflow_id:str, *, session:Session) -> None:
        time_ended = datetime.now(timezone.utc).replace(tzinfo=None)
        if step_id is None:
            workflow_dto = self.workflow_dao.get(workflow_id, session=session)
            assert workflow_dto is not None
            workflow_dto.state = WorkflowState.SUCCEEDED
            workflow_dto.time_ended = time_ended
        else:
            step_dto = self.step_dao.get(step_id, session=session)
            assert step_dto.step_def.type == StepDefType.WORKFLOW
            assert step_dto.invoke_workflow is not None

            step_dto.invoke_workflow.state = WorkflowState.SUCCEEDED
            step_dto.invoke_workflow.time_ended = time_ended

            if step_dto.step_def.is_return_step:
                step_dto.workflow.output = deepcopy(step_dto.invoke_workflow.output)
        session.flush()


    ############################################################
    # 将一个步骤的状态设置成FAILED
    ############################################################
    def set_step_state_failed(self, step_id:str, *, session:Session) -> None:
        time_ended = datetime.now(timezone.utc).replace(tzinfo=None)
        step_dto = self.step_dao.get(step_id, session=session)
        assert step_dto.step_def.type == StepDefType.TASK
        assert step_dto.invoke_task is not None

        step_dto.invoke_task.state = TaskState.FAILED
        step_dto.invoke_task.time_ended = time_ended
        step_dto.invoke_task.output = None
        session.flush()

    ############################################################
    # 将一个Workflow的状态设置成FAILED
    ############################################################
    def set_workflow_state_failed(self, workflow_id:str, *, session:Session) -> None:
        workflow_dto = self.workflow_dao.get(workflow_id, session=session)
        workflow_dto.state = WorkflowState.FAILED
        workflow_dto.time_ended = datetime.now(timezone.utc).replace(tzinfo=None)
        session.flush()

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

    ############################################################
    # 等待一个workflow进入RUN_REQUESTED状态
    # 如果再规定时间内workflow进入了RUN_REQUESTED状态，则返回True
    # 否则返回False
    ############################################################
    async def wait_for_workflow_in_run_requested_state(self, workflow_id:str, timeout_in_seconds:int, *, engine:Engine) -> bool:
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        while True:
            with Session(engine) as session:
                workflow_dto = self.workflow_dao.get(workflow_id, session=session)
                if workflow_dto is not None and workflow_dto.state == WorkflowState.RUN_REQUESTED:
                    return True
            await asyncio.sleep(1)
            if datetime.now(timezone.utc).replace(tzinfo=None) - start_time > timedelta(seconds=timeout_in_seconds):
                return False

    ############################################################
    # 等待一个task进入RUN_REQUESTED状态
    # 如果再规定时间内task进入了RUN_REQUESTED状态，则返回True
    # 否则返回False
    ############################################################
    async def wait_for_task_in_run_requested_state(self, step_id:str, timeout_in_seconds:int, *, engine:Engine) -> bool:
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        while True:
            with Session(engine) as session:
                step_dto = self.step_dao.get(step_id, session=session)
                if step_dto is not None and step_dto.invoke_task is not None and step_dto.invoke_task.state == TaskState.RUN_REQUESTED:
                    return True
            await asyncio.sleep(1)
            if datetime.now(timezone.utc).replace(tzinfo=None) - start_time > timedelta(seconds=timeout_in_seconds):
                return False

    ############################################################
    # 解析步骤的输入参数
    ############################################################
    def resolve_step_input(self, workflow:Workflow, step:Step) -> dict|None:
        logger.debug(f"WorkflowService.resolve_step_input: enter, workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}")

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
        logger.debug(f"WorkflowService.resolve_step_input: workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}, step_input_value = {step_input_value}, exit")
        return step_input_value

    ############################################################
    # 创建步骤对应的task或者workflow
    ############################################################
    def create_task_or_nested_workflow_for_step(self, step_input_value:dict|None, workflow:Workflow, step:Step, *, session:Session) -> None:
        logger.debug(f"WorkflowService.create_task_or_nested_workflow_for_step: enter, workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}")
        if step.step_def.type == StepDefType.TASK:
            task_dto = self.task_dao.save(
                TaskDTO(
                    workflow_id = workflow.id,
                    task_def_id = step.step_def.invoke_task_def.id,
                    state = TaskState.CREATED,
                    input = deepcopy(step_input_value),
                    output = None
                ),
                session = session
            )
            logger.debug(f"WorkflowService.create_task_or_nested_workflow_for_step: workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}, task({task_dto.id}) is created")
            step_dto = self.step_dao.get(step.id, session=session)
            step_dto.invoke_task_id = task_dto.id
            session.flush()
        elif step.step_def.type == StepDefType.WORKFLOW:
            create_workflow_details = CreateWorkflowDetails(
                parent_id=workflow.id,
                workflow_def_nv = NameAndVersion(
                    name = step.step_def.invoke_workflow_def.name,
                    version = step.step_def.invoke_workflow_def.version,
                ),
                description = f"{workflow.title}/{step.step_def.key}",
                title = f"{workflow.title}/{step.step_def.key}",
                input = step_input_value
            )
            workflow = self._create_workflow_in_db(create_workflow_details, session=session)
            logger.debug(f"WorkflowService.prepare_execute_step: workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}, workflow({workflow.id}) is created")
            step_dto = self.step_dao.get(step.id, session=session)
            step_dto.invoke_workflow_id = workflow.id
            session.flush()
        logger.debug(f"WorkflowService.create_task_or_nested_workflow_for_step: workflow_id={workflow.id}, step={step.id}, step_key={step.step_def.key}, exit")



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

class EventService:
    event_dao: EventDAO
    mapper: Mapper

    def __init__(self):
        self.event_dao = EventDAO()
        self.mapper = Mapper()

    ############################################################
    # 列出全部根一个workflow相关的Event
    ############################################################
    def list(self, workflow_id:str, *, session:Session) -> List[Event]:
        return [
            self.mapper.event_to_model(event_dto) \
                for event_dto in self.event_dao.list(workflow_id, session=session)
        ]
    
    def create(self, create_event_details:CreateEventDetails, *, session:Session) -> Event:
        event_dto = EventDTO(
            type = create_event_details.type,
            workflow_id = create_event_details.workflow_id,
            step_id = create_event_details.step_id,
            task_id = create_event_details.task_id,
            message = create_event_details.message
        )
        event_dto = self.event_dao.save(event_dto, session=session)
        return self.mapper.event_to_model(event_dto)

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
            is_return_step = step_def_dto.is_return_step,
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
            input = deepcopy(workflow_dto.input),
            output = deepcopy(workflow_dto.output),
            state = workflow_dto.state,
            time_created = workflow_dto.time_created,
            time_started = workflow_dto.time_started,
            time_ended = workflow_dto.time_ended
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
    
    def event_to_model(self, event_dto: EventDTO|None) -> Event|None:
        return None if event_dto is None else Event(
            id = event_dto.id,
            event_time=event_dto.event_time,
            type = event_dto.type,
            workflow_id=event_dto.workflow_id,
            step_id = event_dto.step_id,
            task_id = event_dto.task_id,
            message = event_dto.message
        )
    
    def task_to_model(self, task_dto:TaskDTO) -> Task:
        return Task(
            id = task_dto.id,
            task_def = self.task_def_to_model(task_dto.task_def),
            state = task_dto.state,
            input = deepcopy(task_dto.input),
            output = deepcopy(task_dto.output),
            time_created = task_dto.time_created,
            time_started = task_dto.time_started,
            time_ended = task_dto.time_ended
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
        
