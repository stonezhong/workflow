import logging.config
import pytest
import yaml
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from zworkflow.dal.dtos import create_all_tables
from zworkflow.core.services import WorkflowDefService, WorkflowService
from zworkflow.dal.daos import TaskDefDAO, WorkflowDefDAO, StepDefDAO, StepDefDepDAO, SchemaDAO, StepDAO, TaskDAO, WorkflowDAO

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
def task_def_dao():
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
