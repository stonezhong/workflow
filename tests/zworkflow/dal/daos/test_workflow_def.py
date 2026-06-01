import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import create_all_tables, TaskDefDTO, WorkflowDefDTO, StepDefDTO, StepDefType, StepDefDepDTO
from zworkflow.dal.daos import TaskDefDAO, WorkflowDefDAO, StepDefDAO, StepDefDepDAO, WorkflowDAO

def is_task_def_dto_same(task_def_dto1: TaskDefDTO, task_def_dto2: TaskDefDTO):
    if task_def_dto1 is None and task_def_dto2 is None:
        return True
    if task_def_dto1 is None and task_def_dto2 is not None:
        return False
    if task_def_dto1 is not None and task_def_dto2 is None:
        return False
    if task_def_dto1.id != task_def_dto2.id:
        return False
    if task_def_dto1.name != task_def_dto2.name:
        return False
    if task_def_dto1.version != task_def_dto2.version:
        return False
    if task_def_dto1.description != task_def_dto2.description:
        return False
    if task_def_dto1.title != task_def_dto2.title:
        return False
    if task_def_dto1.input_schema != task_def_dto2.input_schema:
        return False
    if task_def_dto1.output_schema != task_def_dto2.output_schema:
        return False
    return True

def test_workflow_def_dao(
        engine:Engine, 
        task_def_dao: TaskDefDAO, 
        workflow_def_dao:WorkflowDefDAO, 
        step_def_dao:StepDefDAO,
        step_def_dep_dao:StepDefDepDAO
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

            # 现在添加step1, step2
            step_def1_dao = step_def_dao.save(
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
            step_def2_dao = step_def_dao.save(
                StepDefDTO(
                    workflow_def_id = workflow_def_dto.id,
                    key = "step2",
                    title = "step2",
                    description = "step2",
                    type = StepDefType.TASK,
                    input = '{"x": 2, "y": 3}',
                    invoke_task_def_id = task_def_dto.id,
                    invoke_workflow_def_id = None
                ),
                session = session
            )

            # 添加依赖关系
            step_def_dep_dto = step_def_dep_dao.save(
                StepDefDepDTO(
                    workflow_def_id = workflow_def_dto.id,
                    source_step_def_key = "step1",
                    destination_step_def_key = "step2"
                ),
                session = session
            )

            # 现在重新加载workflow_def，对字段逐一检查
            workflow_def_dto = workflow_def_dao.get(
                workflow_def_dto.id,
                session = session
            )
            assert workflow_def_dto.name == "myworkflow-def"
            assert workflow_def_dto.version == "1.0"
            assert workflow_def_dto.description == "Blah"
            assert workflow_def_dto.title == "Blah"
            assert workflow_def_dto.input_schema is None
            assert workflow_def_dto.output_schema is None

            assert len(workflow_def_dto.steps) == 2

            saving_steps = sorted([step_def1_dao, step_def2_dao], key=lambda i:i.id)
            saved_steps = sorted(workflow_def_dto.steps, key=lambda i:i.id)
            for i in range(0, len(workflow_def_dto.steps)):
                assert saving_steps[i].id == saved_steps[i].id
                
                assert saving_steps[i].workflow_def_id == workflow_def_dto.id
                assert saved_steps[i].workflow_def_id == workflow_def_dto.id
                assert saving_steps[i].workflow_def is workflow_def_dto
                assert saved_steps[i].workflow_def is workflow_def_dto

                assert saving_steps[i].key == saved_steps[i].key
                assert saving_steps[i].title == saved_steps[i].title
                assert saving_steps[i].description == saved_steps[i].description
                assert saving_steps[i].type == StepDefType.TASK
                assert saved_steps[i].type == StepDefType.TASK

                
                assert saving_steps[i].invoke_task_def_id == task_def_dto.id
                assert saved_steps[i].invoke_task_def_id == task_def_dto.id
                assert is_task_def_dto_same(saving_steps[i].invoke_task_def, task_def_dto)
                assert is_task_def_dto_same(saved_steps[i].invoke_task_def, task_def_dto)
                
                assert saving_steps[i].invoke_workflow_def_id is None
                assert saving_steps[i].invoke_workflow_def is None
                assert saved_steps[i].invoke_workflow_def_id is None
                assert saved_steps[i].invoke_workflow_def is None

            assert len(workflow_def_dto.step_deps) == 1
            assert workflow_def_dto.step_deps[0].workflow_def_id == workflow_def_dto.id
            assert workflow_def_dto.step_deps[0].workflow_def == workflow_def_dto
            assert workflow_def_dto.step_deps[0].source_step_def_key == "step1"
            assert workflow_def_dto.step_deps[0].destination_step_def_key == "step2"

    with Session(engine) as session:
        with session.begin() as transaction:
            workflow_dtos = workflow_def_dao.list(session=session)
            assert len(workflow_dtos) == 1

def test_workflow_def_dao_get_by_name_and_version(engine:Engine, workflow_dao: WorkflowDAO, workflow_def_dao:WorkflowDefDAO, simple_saved_workflow_id:str):
    with Session(engine) as session:
        with session.begin():
            workflow_dto = workflow_dao.get(simple_saved_workflow_id, session=session)

            workflow_def_dto = workflow_def_dao.get_by_name_and_version(
                workflow_dto.workflow_def.name, 
                workflow_dto.workflow_def.version,
                session=session
            )
            assert workflow_def_dto is not None
            assert workflow_def_dto.id == workflow_dto.workflow_def.id
            assert workflow_def_dto.name == workflow_dto.workflow_def.name
            assert workflow_def_dto.version == workflow_dto.workflow_def.version
