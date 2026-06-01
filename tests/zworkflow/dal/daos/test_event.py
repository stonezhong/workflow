import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import EventDTO, EventType
from zworkflow.dal.daos import EventDAO

def test_event_dao(engine:Engine, event_dao:EventDAO, simple_saved_workflow_id:str):
    # 保存一个Event
    with Session(engine) as session:
        with session.begin():
            event_dto = EventDTO(
                type = EventType.WORKFLOW_SUBMITTED,
                message = "Hi",
                workflow_id = simple_saved_workflow_id,
                step_id = None,
                task_id = None
            )
            event_dto = event_dao.save(event_dto, session=session)
            event_id = event_dto.id


    # 然后加载
    with Session(engine) as session:
        with session.begin():
            event_dto = event_dao.get(event_id, session=session)
            assert event_dto.type == EventType.WORKFLOW_SUBMITTED
            assert event_dto.message == "Hi"
            assert event_dto.workflow_id == simple_saved_workflow_id
            assert event_dto.step_id is None
            assert event_dto.task_id is None

    # 列表，获得一个event_dto
    with Session(engine) as session:
        with session.begin():
            event_dtos = event_dao.list(workflow_id=simple_saved_workflow_id, session=session)

            assert len(event_dtos) == 1
