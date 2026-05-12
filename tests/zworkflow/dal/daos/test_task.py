import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import create_all_tables, TaskDefDTO, WorkflowDefDTO, StepDefDTO, StepDefType, \
    WorkflowDTO, WorkflowState, StepDTO, TaskDTO, TaskState
from zworkflow.dal.daos import TaskDefDAO, WorkflowDefDAO, StepDefDAO, WorkflowDAO, StepDAO, TaskDAO


def test_task_dao(
        engine:Engine, 
        task_def_dao: TaskDefDAO, 
        workflow_def_dao:WorkflowDefDAO, 
        step_def_dao:StepDefDAO,
        workflow_dao:WorkflowDAO,
        step_dao: StepDAO,
        task_dao: TaskDAO
):
    # task是附属在workflow上的
    with Session(engine) as session:
        with session.begin() as transaction:
            # 创建一个TaskDefDTO，它会被引用
            task_def_dto = task_def_dao.save(
                TaskDefDTO(
                    name = "foo",
                    version = "1.0",
                    description="description",
                    title = "title"
                ),
                session=session
            )

            # 创建一个WorkflowDefDTO
            workflow_def_dto = workflow_def_dao.save(
                WorkflowDefDTO(
                    name = "myworkflow-def",
                    version = "1.0",
                    description = "Blah",
                    title = "Blah",
                    input_schema = None,
                    output_schema = None
                ),
                session = session
            )

            # 现在添加step1
            step_def_dto = step_def_dao.save(
                StepDefDTO(
                    workflow_def_id = workflow_def_dto.id,
                    key = "step1",
                    title = "step1",
                    description = "step1",
                    type = StepDefType.TASK,
                    input = '{"x": 1, "y": 2}',
                    invoke_task_def_id = task_def_dto.id,
                    invoke_workflow_def_id = None
                ),
                session = session
            )

            # 现在创建一个workflow
            workflow_dto = workflow_dao.save(
                WorkflowDTO(
                    workflow_def_id = workflow_def_dto.id,
                    description = "my workflow",
                    title = "my workflow",
                    state = WorkflowState.CREATED,
                    input = {"x": 1, "y": 1}
                ),
                session = session
            )
            task_dto = task_dao.save(
                TaskDTO(
                    workflow_id = workflow_dto.id,
                    task_def_id = task_def_dto.id,
                    state = TaskState.CREATED,
                    input = {"x": 1, "y": 1}
                ),
                session = session
            )

            step_dto = step_dao.save(
                StepDTO(
                    workflow_id = workflow_dto.id,
                    step_def_id = step_def_dto.id,
                    invoke_task_id = task_dto.id,
                    invoke_workflow_id=None
                ),
                session = session
            )

            assert task_dto.id is not None
            assert task_dto.workflow_id == workflow_dto.id
            assert task_dto.task_def_id == task_def_dto.id
            assert task_dto.state == TaskState.CREATED
            assert task_dto.input == {"x": 1, "y": 1}

            task_id = task_dto.id
            workflow_id = workflow_dto.id
            task_def_id = task_def_dto.id


    with Session(engine) as session:
        with session.begin() as transaction:
            # 重新加载task
            task_dto = task_dao.get(task_id, session=session)

            assert task_dto.id == task_id
            assert task_dto.workflow_id == workflow_id
            assert task_dto.task_def_id == task_def_id
            assert task_dto.state == TaskState.CREATED
            assert task_dto.input == {"x": 1, "y": 1}

    with Session(engine) as session:
        with session.begin() as transaction:
            task_dtos = task_dao.list(workflow_id=workflow_id, session=session)
            task_dto = task_dtos[0]

            assert task_dto.id == task_id
            assert task_dto.workflow_id == workflow_id
            assert task_dto.task_def_id == task_def_id
            assert task_dto.state == TaskState.CREATED
            assert task_dto.input == {"x": 1, "y": 1}

