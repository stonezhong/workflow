import logging.config
import pytest
import yaml
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import create_all_tables, WorkflowDTO, TaskDefDTO, WorkflowDefDTO, \
  StepDefDTO, StepDefType, WorkflowState, TaskDTO, TaskState, StepDTO, StepDefDepDTO
from zworkflow.core.services import WorkflowDefService, WorkflowService, EventService
from zworkflow.dal.daos import TaskDefDAO, WorkflowDefDAO, StepDefDAO, \
  StepDefDepDAO, SchemaDAO, StepDAO, TaskDAO, WorkflowDAO, EventDAO

###################################################
# 这么做的目的是，每个测试函数都会有一个全新的数据库
# 不同的测试函数之间互相不干扰
###################################################
@pytest.fixture(scope="function")  # shared across all tests in the module
def engine():
    with PostgresContainer("postgres:16") as pg:
        engine = create_engine(pg.get_connection_url())
        create_all_tables(engine)
        yield engine

@pytest.fixture(scope="function")  # shared across all tests in the module
def workflow_def_service() -> WorkflowDefService:
    return WorkflowDefService()

@pytest.fixture(scope="function")  # shared across all tests in the module
def workflow_service() -> WorkflowService:
    return WorkflowService()

@pytest.fixture(scope="function")  # shared across all tests in the module
def event_service() -> EventService:
    return EventService()

@pytest.fixture(scope="function")  # shared across all tests in the module
def task_def_dao() -> TaskDefDAO:
    return TaskDefDAO()

@pytest.fixture(scope="function")
def workflow_def_dao() -> WorkflowDefDAO:
    return WorkflowDefDAO()

@pytest.fixture(scope="function")
def step_def_dao() -> StepDefDAO:
    return StepDefDAO()

@pytest.fixture(scope="function")
def step_def_dep_dao() -> StepDefDepDAO:
    return StepDefDepDAO()

@pytest.fixture(scope="function")
def schema_dao() -> SchemaDAO:
    return SchemaDAO()

@pytest.fixture(scope="function")
def step_dao() -> StepDAO:
    return StepDAO()

@pytest.fixture(scope="function")
def task_dao() -> TaskDAO:
    return TaskDAO()

@pytest.fixture(scope="function")
def workflow_dao() -> WorkflowDAO:
    return WorkflowDAO()

@pytest.fixture(scope="function")
def event_dao() -> EventDAO:
    return EventDAO()

@pytest.fixture(scope="function")
def simple_saved_workflow_id(
    engine:Engine, 
    task_def_dao:TaskDefDAO, 
    workflow_def_dao: WorkflowDefDAO,
    workflow_dao: WorkflowDAO,
    task_dao: TaskDAO,
    step_dao: StepDAO,
    simple_workflow_def_id: str
) -> str:
    with Session(engine) as session:
        with session.begin():
            workflow_def_dto = workflow_def_dao.get(simple_workflow_def_id, session=session)
            task_def_dto = task_def_dao.get_by_name_and_vesion("foo", "1.0", session=session)

            step1_def_dto = workflow_def_dto.steps[0]
            step2_def_dto = workflow_def_dto.steps[1]

            # 现在创建一个workflow
            workflow_dto = workflow_dao.save(
                WorkflowDTO(
                    workflow_def_id = simple_workflow_def_id,
                    description = "my workflow",
                    title = "my workflow",
                    state = WorkflowState.CREATED,
                    input = {"a": 1, "b": 2, "c": 3, "d": 4}
                ),
                session = session
            )
            # 创建step1
            task1_dto = task_dao.save(
                TaskDTO(
                    workflow_id = workflow_dto.id,
                    task_def_id = task_def_dto.id,
                    state = TaskState.RUNNING,
                    input = {"x": 1, "y": 2}
                ),
                session = session
            )
            step_dao.save(
                StepDTO(
                    workflow_id = workflow_dto.id,
                    step_def_id = step1_def_dto.id,
                    invoke_task_id = task1_dto.id,
                    invoke_workflow_id=None
                ),
                session = session
            )
            # 创建step2
            task2_dto = task_dao.save(
                TaskDTO(
                    workflow_id = workflow_dto.id,
                    task_def_id = task_def_dto.id,
                    state = TaskState.RUNNING,
                    input = {"x": 3, "y": 4}
                ),
                session = session
            )
            step_dao.save(
                StepDTO(
                    workflow_id = workflow_dto.id,
                    step_def_id = step2_def_dto.id,
                    invoke_task_id = task2_dto.id,
                    invoke_workflow_id=None
                ),
                session = session
            )

            return workflow_dto.id

# 一个简单的workflow definition
@pytest.fixture(scope="function")
def simple_workflow_def_id(
    engine:Engine, 
    task_def_dao:TaskDefDAO, 
    workflow_def_dao: WorkflowDefDAO,
    step_def_dao: StepDefDAO,
    step_def_dep_dao: StepDefDepDAO
) -> str:
    with Session(engine) as session:
        with session.begin():
            workflow_input_schema = {
                "type": "object",
                "required": ["a", "b", "c", "d"],
                "properties": {
                    "a": {
                        "type": "integer"
                    },
                    "b": {
                        "type": "integer"
                    },
                    "c": {
                        "type": "integer"
                    },
                    "d": {
                        "type": "integer"
                    }
                },
                "additionalProperties": False
            }
            workflow_output_schema = {
                "type": "object",
                "required": ["result"],
                "properties": {
                    "result": {
                        "type": "integer"
                    }
                },
                "additionalProperties": False
            }

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

    
            # 创建一个TaskDefDTO，它会被引用
            task_def_dto = task_def_dao.save(
                TaskDefDTO(
                    name = "foo",
                    version = "1.0",
                    description="description",
                    title = "title",
                    input_schema = task_input_schema,
                    output_schema = task_output_schema
                ),
                session=session
            )

            # 创建一个WorkflowDefDTO
            workflow_def_dto = workflow_def_dao.save(
                WorkflowDefDTO(
                    name = "simple-workflow-def",
                    version = "1.0",
                    description = "Blah",
                    title = "Blah",
                    input_schema = workflow_input_schema,
                    output_schema = workflow_output_schema
                ),
                session = session
            )

            # 现在定义step1
            step_def_dao.save(
                StepDefDTO(
                    workflow_def_id = workflow_def_dto.id,
                    key = "step1",
                    title = "step1",
                    description = "step1",
                    type = StepDefType.TASK,
                    input = '{"x": workflow.input.a, "y": workflow.input.b}',
                    invoke_task_def_id = task_def_dto.id,
                    invoke_workflow_def_id = None
                ),
                session = session
            )

            # 现在定义step2
            step_def_dao.save(
                StepDefDTO(
                    workflow_def_id = workflow_def_dto.id,
                    key = "step2",
                    title = "step2",
                    description = "step2",
                    type = StepDefType.TASK,
                    input = '{"x": workflow.input.c, "y": workflow.input.d}',
                    invoke_task_def_id = task_def_dto.id,
                    invoke_workflow_def_id = None
                ),
                session = session
            )
            
            step_def_dep_dto = StepDefDepDTO(
                workflow_def_id = workflow_def_dto.id,
                source_step_def_key = "step1",
                destination_step_def_key = "step2"
            )
            step_def_dep_dao.save(step_def_dep_dto, session=session)

            return workflow_def_dto.id

LOGGING_CONFIG = """
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    stream: ext://sys.stdout

loggers:
  urllib3:
    level: WARNING
  testcontainers:
    level: WARNING
  docker:
    level: WARNING
  sqlalchemy.engine:
    level: WARNING
  uvicorn.access:
    level: WARNING
  temporalio.worker:
    level: WARNING
  temporalio.activity:
    level: WARNING

root:
  level: DEBUG
  handlers: [console]
"""
# 如果你需要查看单元测试时候的log，可以开放下面代码
# @pytest.fixture(autouse=True)    # runs for every test automatically
# def setup_logging():
#     logging.config.dictConfig(yaml.safe_load(LOGGING_CONFIG))
