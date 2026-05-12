import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import TaskDefDTO
from zworkflow.dal.daos import TaskDefDAO

def test_task_def_dao(engine:Engine, task_def_dao:TaskDefDAO):
    # 保存一个TaskDefDTO
    with Session(engine) as session:
        with session.begin() as transaction:
            task_def_dto = task_def_dao.save(
                TaskDefDTO(
                    name = "foo",
                    version = "1.0",
                    description="description",
                    title = "title"
                ),
                session=session
            )
            # it should be saved, id should not be None
            # field value shoudl match
            task_def_dto_id = task_def_dto.id
            assert task_def_dto.id is not None
            assert task_def_dto.name == "foo"
            assert task_def_dto.version == "1.0"
            assert task_def_dto.description == "description"
            assert task_def_dto.title == "title"
    
    # Loading the task def, make sure nothing is saved wrong
    with Session(engine) as session:
        task_def_dto = task_def_dao.get(task_def_dto_id, session=session)
        assert task_def_dto.id == task_def_dto_id
        assert task_def_dto.name == "foo"
        assert task_def_dto.version == "1.0"
        assert task_def_dto.description == "description"
        assert task_def_dto.title == "title"
    
    # try to list TaskDef should return one
    with Session(engine) as session:
        task_def_dtos = task_def_dao.list(session=session)
        assert len(task_def_dtos) == 1
        assert task_def_dtos[0].id == task_def_dto.id
        assert task_def_dtos[0].name == task_def_dto.name
        assert task_def_dtos[0].version == task_def_dto.version
        assert task_def_dtos[0].description == task_def_dto.description
        assert task_def_dtos[0].title == task_def_dto.title
