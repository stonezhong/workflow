import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.daos import WorkflowDAO, StepDefDepDAO


def test_step_def_dep(engine:Engine, workflow_dao:WorkflowDAO, step_def_dep_dao:StepDefDepDAO, simple_saved_workflow_id:str):
    with Session(engine) as session:
        with session.begin():
            workflow_dto = workflow_dao.get(simple_saved_workflow_id, session=session)

            # 加载一个step
            step_def_dep_dto = step_def_dep_dao.get(workflow_dto.workflow_def.step_deps[0].id, session=session)
            assert step_def_dep_dto is not None
            assert step_def_dep_dto.id == workflow_dto.workflow_def.step_deps[0].id

            step_def_dep_dtos = step_def_dep_dao.list(workflow_def_id = workflow_dto.workflow_def_id, session=session)
            assert len(step_def_dep_dtos) == 1

