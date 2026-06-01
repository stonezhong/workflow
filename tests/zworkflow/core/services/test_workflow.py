import logging
logger = logging.getLogger(__name__)

import os
import time
import pytest
import subprocess
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import Session
from zworkflow.core.services import WorkflowService, WorkflowDefService, EventService
from zworkflow.core.models import TaskDef, NameAndVersion, CreateTaskDefDetails, StepDefDepDetails
from zworkflow.core.models import CreateWorkflowDetails, CreateWorkflowDefDetails, CreateWorkflowDefStepDetails
from zworkflow.dal.dtos import create_all_tables, StepDefType, WorkflowState, TaskState
from zworkflow.core.exceptions import WorkflowInputSchemaViolation, FailedToSubmitWorkflow
from zworkflow.dal.daos import TaskDAO, WorkflowDAO

########################################################################
# 这个文件测试WorkflowService
########################################################################

def test_list(engine:Engine, workflow_service: WorkflowService, simple_saved_workflow_id: str):
    with Session(engine) as session:
        with session.begin():
            workflow_def = workflow_service.list(session=session)
            assert len(workflow_def) == 1

@pytest.fixture(scope="function")
def real_engine():
    engine:Engine = create_engine(
        "postgresql+psycopg2://zworkflow:foobar@localhost:5432/testdb",
        connect_args = {}
    )
    create_all_tables(engine)
    yield engine
    engine.dispose()

    

@pytest.fixture
def temporal_server():
    log_dir = os.path.join(os.getcwd(), "sample_worker", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = open(os.path.join(log_dir, "temporal-server.log"), "a+")
    temporal_proc = subprocess.Popen(
        ["temporal", "server", "start-dev", "--ip", "0.0.0.0"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"Temporal dev server is up, pid = {temporal_proc.pid}")

    yield 
    
    print(f"Stopping temporal server")
    temporal_proc.terminate()
    try:
        temporal_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        temporal_proc.kill()
        temporal_proc.wait()
    print(f"temporal server is stopped")

@pytest.fixture
def temporal_worker():
    log_dir = os.path.join(os.getcwd(), "sample_worker", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = open(os.path.join(log_dir, "temporal-worker.log"), "a+")
    # worker_proc = subprocess.Popen(
    #     [
    #         os.path.join(os.environ['VENV_DIR'], 'bin', 'python'),
    #         "-m", 
    #         "zworkflow.executor", 
    #         "--handlers", 
    #         "handlers.yaml"
    #     ],
    #     stdout=log_file,
    #     stderr=subprocess.STDOUT,
    #     text=True,
    #     cwd=os.path.join(os.getcwd(), "sample_worker"),       
    # )
    worker_proc = subprocess.Popen(
        [
            os.path.join(os.environ['VENV_DIR'], 'bin', 'python'),
            "-m", 
            "coverage",
            "run",
            "--data-file",
            os.path.join(os.getcwd(), ".coverage"),
            "-m",
            "zworkflow.executor", 
            "--handlers", 
            "handlers.yaml"
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=os.path.join(os.getcwd(), "sample_worker"),       
    )
    print(f"Temporal worker is up, pid = {worker_proc.pid}")

    yield 
    
    print(f"Stopping temporal worker")
    worker_proc.terminate()
    try:
        worker_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        worker_proc.kill()
        worker_proc.wait()
    print(f"temporal worker is stopped")


########################################################################
# 以下是Integration测试
########################################################################
@pytest.mark.integration
class IntegrationTestSuit:
    __test__ = True

    def cleanup_database(self, real_engine:Engine):
        # 清理数据库
        with Session(real_engine) as session:
            with session.begin():
                session.execute(text("""
                    TRUNCATE TABLE
                        step,
                        task,
                        workflow,
                        step_def,
                        step_def_dep,
                        workflow_def,
                        task_def,
                        schema
                    CASCADE
                """))
        print("tables are truncated")

    # 定义加法任务
    def create_add_task_def(self, real_engine:Engine, workflow_def_service:WorkflowDefService):
        with Session(real_engine) as session:
            with session.begin():
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
                    name = "add",
                    version = "1.0",
                    description="add",
                    title = "add",
                    input_schema=task_input_schema,
                    output_schema=task_output_schema
                )
                workflow_def_service.create_task_def(create_task_def_details, session=session)

    # 定义乘法任务
    def create_mul_task_def(self, real_engine:Engine, workflow_def_service:WorkflowDefService):
        with Session(real_engine) as session:
            with session.begin():
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
                    name = "mul",
                    version = "1.0",
                    description="mul",
                    title = "mul",
                    input_schema=task_input_schema,
                    output_schema=task_output_schema
                )
                workflow_def_service.create_task_def(create_task_def_details, session=session)

    # 定义一个简单的Workflow
    def create_simple_workflow_def(self, real_engine:Engine, workflow_def_service:WorkflowDefService):
        with Session(real_engine) as session:
            with session.begin():
                workflow_input_schema = {
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

                create_workflow_def_details = CreateWorkflowDefDetails(
                    name = "test",
                    version = "1.0",
                    description = "test",
                    title = "test",
                    steps = [
                        CreateWorkflowDefStepDetails(
                            key = "step1",
                            description = "Step 1",
                            title = "Step 1",
                            type = StepDefType.TASK,
                            input = '{"x": workflow.input.x, "y": workflow.input.y}',
                            is_return_step = True,
                            invoke_task_def_nv = NameAndVersion(name="add", version="1.0")
                        )
                    ],
                    step_deps = [ 
                    ],
                    input_schema = workflow_input_schema,
                    output_schema = workflow_output_schema
                )
                workflow_def_service.create_workflow_def(create_workflow_def_details, session=session)

    @pytest.mark.usefixtures("temporal_worker")
    @pytest.mark.usefixtures("temporal_server")
    @pytest.mark.asyncio
    async def test_simple1(
        self, 
        real_engine:Engine, 
        workflow_def_service: WorkflowDefService,
        workflow_service: WorkflowService,
        event_service: EventService
    ):
        print()
        print("###################################################")
        print("# Integration test: create a simple workflow")
        print("# Expect          : workflow created, executed to end successfully")
        print("###################################################")
        print()
        self.cleanup_database(real_engine)

        # 创建加法和乘法任务定义
        self.create_add_task_def(real_engine, workflow_def_service)
        self.create_mul_task_def(real_engine, workflow_def_service)
        # 创建一个简单的Workflow定义
        self.create_simple_workflow_def(real_engine, workflow_def_service)

        # 现在创建一个workflow
        with Session(real_engine) as session:
            with session.begin():
                create_workflow_details = CreateWorkflowDetails(
                    workflow_def_nv = NameAndVersion(
                        name = "test",
                        version = "1.0"
                    ),
                    description = "run test workflow",
                    title = "run test workflow",
                    input = {"x": 1, "y": 2}
                )

                workflow = await workflow_service.create_workflow(create_workflow_details, session = session)
                print(f"Workflow is created, id = {workflow.id}")


        # 等待workflow结束
        for _ in range(10):
            with Session(real_engine) as session:
                with session.begin():
                    workflow = workflow_service.get_workflow(workflow.id, session=session)
            print(f"Workflow state: {workflow.state}")
            if workflow.state in (WorkflowState.SUCCEEDED, WorkflowState.FAILED):
                break
            time.sleep(1)

        # with Session(real_engine) as session:
        #     with session.begin():
        #         events = event_service.list(workflow.id, session=session)
        #         for event in events:
        #             print(f"{event.type}")

        assert workflow.output['result'] == 3


    @pytest.mark.usefixtures("temporal_worker")
    @pytest.mark.usefixtures("temporal_server")
    @pytest.mark.asyncio
    async def test_simple2(
        self, 
        real_engine:Engine, 
        workflow_def_service: WorkflowDefService,
        workflow_service: WorkflowService
    ):
        print()
        print("###################################################")
        print("# Integration test: create a workflow, pass input that violates schema")
        print("# Expect          : create_workflow throws exception")
        print("###################################################")
        print()
        self.cleanup_database(real_engine)

        # 创建加法和乘法任务定义
        self.create_add_task_def(real_engine, workflow_def_service)
        self.create_mul_task_def(real_engine, workflow_def_service)
        # 创建一个简单的Workflow定义
        self.create_simple_workflow_def(real_engine, workflow_def_service)

        # 现在创建一个workflow
        with Session(real_engine) as session:
            with session.begin():
                create_workflow_details = CreateWorkflowDetails(
                    workflow_def_nv = NameAndVersion(
                        name = "test",
                        version = "1.0"
                    ),
                    description = "run test workflow",
                    title = "run test workflow",
                    input = {"t": 1, "y": 2}
                )

                with pytest.raises(WorkflowInputSchemaViolation):
                    await workflow_service.create_workflow(create_workflow_details, session = session)



    @pytest.mark.asyncio
    async def test_simple3(
        self, 
        real_engine:Engine, 
        workflow_def_service: WorkflowDefService,
        workflow_service: WorkflowService,
        event_service: EventService
    ):
        print()
        print("###################################################")
        print("# Integration test: create a simple workflow, temporal service is not up")
        print("# Expect          : create_workflow throws exception")
        print("###################################################")
        print()
        self.cleanup_database(real_engine)

        # 创建加法和乘法任务定义
        self.create_add_task_def(real_engine, workflow_def_service)
        self.create_mul_task_def(real_engine, workflow_def_service)
        # 创建一个简单的Workflow定义
        self.create_simple_workflow_def(real_engine, workflow_def_service)

        # 现在创建一个workflow
        with Session(real_engine) as session:
            with session.begin():
                create_workflow_details = CreateWorkflowDetails(
                    workflow_def_nv = NameAndVersion(
                        name = "test",
                        version = "1.0"
                    ),
                    description = "run test workflow",
                    title = "run test workflow",
                    input = {"x": 1, "y": 2}
                )

                with pytest.raises(FailedToSubmitWorkflow):
                    await workflow_service.create_workflow(create_workflow_details, session = session)

    @pytest.mark.usefixtures("temporal_worker")
    @pytest.mark.usefixtures("temporal_server")
    @pytest.mark.asyncio
    async def test_simple4(
        self, 
        real_engine:Engine, 
        workflow_def_service: WorkflowDefService,
        workflow_service: WorkflowService,
        event_service: EventService
    ):
        print()
        print("###################################################")
        print("# Integration test: retry failed workflow")
        print("# Expect          : retry succeeded")
        print("###################################################")
        print()
        self.cleanup_database(real_engine)

        # 创建加法和乘法任务定义
        self.create_add_task_def(real_engine, workflow_def_service)
        self.create_mul_task_def(real_engine, workflow_def_service)
        # 创建一个简单的Workflow定义
        self.create_simple_workflow_def(real_engine, workflow_def_service)

        # 现在创建一个workflow
        with Session(real_engine) as session:
            with session.begin():
                create_workflow_details = CreateWorkflowDetails(
                    workflow_def_nv = NameAndVersion(
                        name = "test",
                        version = "1.0"
                    ),
                    description = "run test workflow",
                    title = "run test workflow",
                    input = {"x": 1, "y": 2}
                )

                workflow = await workflow_service.create_workflow(create_workflow_details, session = session)
                print(f"Workflow is created, id = {workflow.id}")


        # 等待workflow结束
        for _ in range(10):
            with Session(real_engine) as session:
                with session.begin():
                    workflow = workflow_service.get_workflow(workflow.id, session=session)
            print(f"Workflow state: {workflow.state}")
            if workflow.state in (WorkflowState.SUCCEEDED, WorkflowState.FAILED):
                break
            time.sleep(1)
        
        task_dao = TaskDAO()
        workflow_dao = WorkflowDAO()

        # 现在人为将这个workflow改成FAILED状态
        with Session(real_engine) as session:
            with session.begin():
                workflow_dto = workflow_dao.get(workflow.id, session=session)
                task1_dto = task_dao.get(workflow.steps[0].invoke_task.id, session=session)
                
                task1_dto.state = TaskState.FAILED
                workflow_dto.state = WorkflowState.FAILED
                workflow_dto.output = None
                session.flush()
        
        # 现在重试这个workflow
        with Session(real_engine) as session:
            with session.begin():
                await workflow_service.restart_failed_workflow(workflow.id, session=session)


        # 等待重试结束
        for _ in range(10):
            with Session(real_engine) as session:
                with session.begin():
                    workflow = workflow_service.get_workflow(workflow.id, session=session)
            print(f"Workflow state: {workflow.state}")
            if workflow.state in (WorkflowState.SUCCEEDED, WorkflowState.FAILED):
                break
            time.sleep(1)

        # 确认重试结果正确
        assert workflow.output['result'] == 3
