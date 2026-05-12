import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import StepDefDTO, StepDefType, TaskDefDTO, WorkflowDefDTO
from zworkflow.dal.daos import StepDefDAO, TaskDefDAO, WorkflowDAO

def test_step_def_dao(
        engine:Engine, 
        task_def_dao: TaskDefDAO, 
        step_def_dao:StepDefDAO, 
        workflow_def_dao:WorkflowDAO
):
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
            workflow_def_id = workflow_def_dto.id

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

            # it should be saved, id should not be None
            # field value shoudl match
            step_def_id = step_def_dto.id
            assert step_def_dto.id is not None
            assert step_def_dto.key == "step1"
            assert step_def_dto.title == "step1"
            assert step_def_dto.description == "step1"
            assert step_def_dto.type == StepDefType.TASK
            assert step_def_dto.input == '{"x": 1, "y": 2}'
            assert step_def_dto.invoke_task_def_id == task_def_dto.id
            
            assert step_def_dto.invoke_workflow_def is None
            assert step_def_dto.invoke_workflow_def_id is None

            assert step_def_dto.invoke_task_def.id == task_def_dto.id
            assert step_def_dto.invoke_task_def.name == "foo"
            assert step_def_dto.invoke_task_def.version == "1.0"
            assert step_def_dto.invoke_task_def.description == "description"
            assert step_def_dto.invoke_task_def.title == "title"
            assert step_def_dto.invoke_task_def.input_schema is None
            assert step_def_dto.invoke_task_def.output_schema is None

            task_def_dto_id = task_def_dto.id


    # Loading the step def, make sure nothing is saved wrong
    with Session(engine) as session:
        task_def_dto = task_def_dao.get(task_def_dto_id, session=session)
        step_def_dto = step_def_dao.get(step_def_id, session=session)

        assert step_def_dto.id == step_def_id
        assert step_def_dto.key == "step1"
        assert step_def_dto.title == "step1"
        assert step_def_dto.description == "step1"
        assert step_def_dto.type == StepDefType.TASK
        assert step_def_dto.input == '{"x": 1, "y": 2}'
        assert step_def_dto.invoke_task_def_id == task_def_dto.id
        
        assert step_def_dto.invoke_workflow_def is None
        assert step_def_dto.invoke_workflow_def_id is None

        assert step_def_dto.invoke_task_def.id == task_def_dto.id
        assert step_def_dto.invoke_task_def.name == "foo"
        assert step_def_dto.invoke_task_def.version == "1.0"
        assert step_def_dto.invoke_task_def.description == "description"
        assert step_def_dto.invoke_task_def.title == "title"
        assert step_def_dto.invoke_task_def.input_schema is None
        assert step_def_dto.invoke_task_def.output_schema is None

    # try to list Schema should return one
    with Session(engine) as session:
        task_def_dto = task_def_dao.get(task_def_dto_id, session=session)
        step_def_dtos = step_def_dao.list(workflow_def_id=workflow_def_id, session=session)

        assert len(step_def_dtos) == 1
        step_def_dto = step_def_dtos[0]

        assert step_def_dto.id == step_def_id
        assert step_def_dto.key == "step1"
        assert step_def_dto.title == "step1"
        assert step_def_dto.description == "step1"
        assert step_def_dto.type == StepDefType.TASK
        assert step_def_dto.input == '{"x": 1, "y": 2}'
        assert step_def_dto.invoke_task_def_id == task_def_dto.id
        
        assert step_def_dto.invoke_workflow_def is None
        assert step_def_dto.invoke_workflow_def_id is None

        assert step_def_dto.invoke_task_def.id == task_def_dto.id
        assert step_def_dto.invoke_task_def.name == "foo"
        assert step_def_dto.invoke_task_def.version == "1.0"
        assert step_def_dto.invoke_task_def.description == "description"
        assert step_def_dto.invoke_task_def.title == "title"
        assert step_def_dto.invoke_task_def.input_schema is None
        assert step_def_dto.invoke_task_def.output_schema is None
