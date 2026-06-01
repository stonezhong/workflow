import logging
logger = logging.getLogger(__name__)

import pytest
from unittest.mock import AsyncMock, patch, ANY
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import StepDefType, WorkflowState
from zworkflow.dal.daos import WorkflowDefDAO
from zworkflow.core.services import WorkflowService, WorkflowDefService
from zworkflow.core.models import TaskDef, NameAndVersion, CreateTaskDefDetails, StepDefDepDetails
from zworkflow.core.models import CreateWorkflowDetails, CreateWorkflowDefDetails, CreateWorkflowDefStepDetails
from zworkflow.core.exceptions import InvalidJSONSchema, BadInput

########################################################################
# 这个文件测试WorkflowDefService
########################################################################

def is_task_def_same(task_def1: TaskDef|None, task_def2: TaskDef|None) -> bool:
    if task_def1 is None and task_def2 is None:
        return True
    if task_def1 is None and task_def2 is not None:
        return False
    if task_def1 is not None and task_def2 is None:
        return False
    if task_def1.id != task_def2.id:
        return False
    if task_def1.name != task_def2.name:
        return False
    if task_def1.version != task_def2.version:
        return False
    if task_def1.description != task_def2.description:
        return False
    if task_def1.title != task_def2.title:
        return False
    if task_def1.input_schema != task_def2.input_schema:
        return False
    if task_def1.output_schema != task_def2.output_schema:
        return False
    return True

# 测试WorkflowDefService.list
def test_list(engine:Engine, workflow_def_service: WorkflowDefService, simple_workflow_def_id: str):
    with Session(engine) as session:
        with session.begin():
            workflow_defs = workflow_def_service.list(session=session)
            assert len(workflow_defs) == 1
            workflow_def = workflow_defs[0]
            assert workflow_def.id == simple_workflow_def_id

# 测试WorkflowDefService.list
def test_get_by_name_and_version(engine:Engine, workflow_def_service: WorkflowDefService, simple_workflow_def_id: str):
    with Session(engine) as session:
        with session.begin():
            workflow_def = workflow_def_service.get_by_name_and_version(
                name = "simple-workflow-def", version = "1.0", session = session
            )
            assert workflow_def is not None

# 测试WorkflowDefService.get_workflow_def
def test_get_workflow_def(engine:Engine, workflow_def_service: WorkflowDefService, simple_workflow_def_id: str):
    with Session(engine) as session:
        with session.begin():
            workflow_def = workflow_def_service.get_workflow_def(simple_workflow_def_id, session=session)
            assert workflow_def is not None
            assert workflow_def.id == simple_workflow_def_id

# 测试WorkflowDefService.list_tasks
def test_list_tasks(engine:Engine, workflow_def_service: WorkflowDefService, simple_workflow_def_id: str):
    with Session(engine) as session:
        with session.begin():
            task_defs = workflow_def_service.list_tasks(session=session)
            assert len(task_defs) == 1
            assert task_defs[0].name == "foo"
            assert task_defs[0].version == "1.0"

# 测试WorkflowDefService.get_task_def
def test_get_task_def(engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO, simple_workflow_def_id: str):
    with Session(engine) as session:
        with session.begin():
            workflow_def_dto = workflow_def_dao.get(simple_workflow_def_id, session=session)

            task_def_id = workflow_def_dto.steps[0].invoke_task_def.id
            task_def = workflow_def_service.get_task_def(task_def_id, session=session)
            assert task_def is not None
            assert task_def.id == task_def_id
            assert task_def.name == "foo"
            assert task_def.version == "1.0"
            assert task_def.description == "description"
            assert task_def.title == "title"
            assert task_def.input_schema is not None
            assert task_def.output_schema is not None

class CreateTaskDef:
    __test__ = True

    # 测试WorkflowDefService.create_task_def
    def test_successful(self, engine:Engine, workflow_def_service: WorkflowDefService):
        with Session(engine) as session:
            with session.begin():
                # 成功创建task def的测试
                task_input_schema = {
                    "type": "object",
                    "required": ["x", "y"],
                    "properties": {
                        "x": {
                            "type": "integer"
                        },
                        "y": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }
                task_output_schema = {
                    "type": "object",
                    "required": ["result"],
                    "properties": {
                        "result": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }

                create_task_def_details = CreateTaskDefDetails(
                    name = "foo",
                    version = "1.0",
                    description="blah-d",
                    title = "blah-t",
                    input_schema=task_input_schema,
                    output_schema=task_output_schema
                )
                task_def = workflow_def_service.create_task_def(create_task_def_details, session=session)
                assert task_def is not None
                assert task_def.name == "foo"
                assert task_def.version == "1.0"
                assert task_def.description == "blah-d"
                assert task_def.title == "blah-t"
                assert task_def.input_schema == task_input_schema
                assert task_def.output_schema == task_output_schema

    # 测试WorkflowDefService.create_task_def
    def test_bad_input_schema(self, engine:Engine, workflow_def_service: WorkflowDefService):
        with Session(engine) as session:
            with session.begin():
                # 模拟输入schema有错
                task_input_schema = {
                    "type": "object1",
                    "required": ["x", "y"],
                    "properties": {
                        "x": {
                            "type": "integer"
                        },
                        "y": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }
                task_output_schema = {
                    "type": "object",
                    "required": ["result"],
                    "properties": {
                        "result": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }

                create_task_def_details = CreateTaskDefDetails(
                    name = "foo",
                    version = "1.0",
                    description="blah-d",
                    title = "blah-t",
                    input_schema=task_input_schema,
                    output_schema=task_output_schema
                )
                with pytest.raises(InvalidJSONSchema):
                    workflow_def_service.create_task_def(create_task_def_details, session=session)

    # 测试WorkflowDefService.create_task_def
    def test_bad_output_schema(self, engine:Engine, workflow_def_service: WorkflowDefService):
        with Session(engine) as session:
            with session.begin():
                # 模拟输出schema有错
                task_input_schema = {
                    "type": "object",
                    "required": ["x", "y"],
                    "properties": {
                        "x": {
                            "type": "integer"
                        },
                        "y": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }
                task_output_schema = {
                    "type": "object1",
                    "required": ["result"],
                    "properties": {
                        "result": {
                            "type": "integer"
                        }
                    },
                    "additionalProperties": False
                }

                create_task_def_details = CreateTaskDefDetails(
                    name = "foo",
                    version = "1.0",
                    description="blah-d",
                    title = "blah-t",
                    input_schema=task_input_schema,
                    output_schema=task_output_schema
                )
                with pytest.raises(InvalidJSONSchema):
                    workflow_def_service.create_task_def(create_task_def_details, session=session)

class CreateWorkflowDef:
    __test__ = True

    input_schema = {
        "type": "object",
        "required": ["x", "y"],
        "properties": {
            "x": {
                "type": "integer"
            },
            "y": {
                "type": "integer"
            }
        },
        "additionalProperties": False
    }
    output_schema = {
        "type": "object",
        "required": ["result"],
        "properties": {
            "result": {
                "type": "integer"
            }
        },
        "additionalProperties": False
    }

    def create_task_def(self, workflow_def_service:WorkflowDefService, session:Session) -> TaskDef:
        create_task_def_details = CreateTaskDefDetails(
            name = "foo",
            version = "1.0",
            description="blah-d",
            title = "blah-t",
            input_schema=self.input_schema,
            output_schema=self.output_schema
        )
        return workflow_def_service.create_task_def(create_task_def_details, session=session)

    def test_successful(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                task_def = self.create_task_def(workflow_def_service, session)
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = False,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        ),
                        CreateWorkflowDefStepDetails(
                            key = "step2",
                            description = "step2-d",
                            title = "step2-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        ),
                    ],
                    step_deps = [ 
                        StepDefDepDetails(source_step_def_key = "step1",destination_step_def_key = "step2") 
                    ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_successful_with_nested_workflow(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO, simple_workflow_def_id:str):
        with Session(engine) as session:
            with session.begin():
                sample_workflow_def_dto = workflow_def_dao.get(simple_workflow_def_id, session=session)
                assert sample_workflow_def_dto is not None

                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.WORKFLOW,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = False,
                            invoke_workflow_def_nv = NameAndVersion(name=sample_workflow_def_dto.name, version=sample_workflow_def_dto.version)
                        ),
                    ],
                    step_deps = [  ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_dup_step_key(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                task_def = self.create_task_def(workflow_def_service, session)
                # 重复的step key，期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        ),
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        )
                    ],
                    step_deps = [ ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)
 
    def test_using_undefined_step_key_in_source(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                task_def = self.create_task_def(workflow_def_service, session)
                # step_def_dep出现未定义的step key，期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        )
                    ],
                    step_deps = [ StepDefDepDetails(source_step_def_key = "step2",destination_step_def_key = "step1") ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_using_undefined_step_key_in_destination(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                task_def = self.create_task_def(workflow_def_service, session)
                # step_deps中，目标出现非法step key，期待期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name=task_def.name, version=task_def.version)
                        )
                    ],
                    step_deps = [ StepDefDepDetails(source_step_def_key = "step1",destination_step_def_key = "step2") ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_task_step_without_nv(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                # task step 未定义 invoke_task_def_nv，期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = None
                        )
                    ],
                    step_deps = [  ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_task_step_with_undefined_nv(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                # invoke_task_def_nv 指向未定义的task def，期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def2",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name="undefined", version="9.9")
                        )
                    ],
                    step_deps = [  ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_nested_workflow_step_without_nv(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                # task step 未定义 invoke_workflow_def_nv
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.WORKFLOW,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_workflow_def_nv = None
                        )
                    ],
                    step_deps = [  ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    def test_nested_workflow_step_with_undefined_nv(self, engine:Engine, workflow_def_service: WorkflowDefService, workflow_def_dao:WorkflowDefDAO):
        with Session(engine) as session:
            with session.begin():
                # invoke_workflow_def_nv 指向未定义的workflow def，期待异常
                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "my-test-workflow-def2",
                    version = "1.0",
                    description = "blah-d",
                    title = "blah-t",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "step1-d",
                            title = "step1-t",
                            type = StepDefType.WORKFLOW,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_workflow_def_nv = NameAndVersion(name="undefined", version="9.9")
                        )
                    ],
                    step_deps = [  ],
                    input_schema = self.input_schema,
                    output_schema = self.output_schema
                )
                with pytest.raises(BadInput):
                    workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

