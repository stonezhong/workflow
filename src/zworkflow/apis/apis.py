from __future__ import annotations

from typing import List
import logging.config
import logging
logger = logging.getLogger(__name__)

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from zworkflow.app_config import app_config
from zworkflow.dal.dtos import create_all_tables
import zworkflow.core.exceptions as core_exceptions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    logging.config.dictConfig(app_config.logging)

    logger.info("zworkflow service startup ...")

    logger.info(f"create database engine, url = {app_config.database.url}, connect_args={app_config.database.connect_args}")
    engine:Engine = create_engine(app_config.database.url, connect_args=app_config.database.connect_args)
    if app_config.database.create_tables:
        create_all_tables(engine)
        logger.info("database tables are created!")

    app.state.engine = engine

    yield # app is running, handling requests

    # ---- shutdown ----
    logger.info("zworkflow service shutdown ...")
    app.state.engine.dispose()

app = FastAPI(lifespan=lifespan)




from zworkflow.apis.models import APIWorkflowDef, APICreateWorkflowDefDetails, APITaskDef, APICreateTaskDefDetails, APIWorkflow, \
    APICreateWorkflowDetails, APISchema, APICreateSchemaDetails, APIEvent
from zworkflow.apis.mapper import APIMapper
from zworkflow.core.services import WorkflowDefService, WorkflowService, SchemaService, EventService
from zworkflow.core.exceptions import TaskDefNotFound, WorkflowDefNotFound, WorkflowNotFound, SchemaNotFound

def get_db():
    with Session(app.state.engine) as session:
        with session.begin():
            yield session

api_mapper: APIMapper = APIMapper()
workflow_def_service: WorkflowDefService = WorkflowDefService()
workflow_service: WorkflowService = WorkflowService()
schema_service: SchemaService = SchemaService()
event_service: EventService = EventService()

#############################################################
# Workflow Def APIs
#############################################################
@app.get(
    "/workflow_defs",
    tags = ["WorkflowDef"],
    summary="List all workflow definitions",
    description = "List all workflow definitions"
)
async def workflow_def_list(session: Session = Depends(get_db)) -> List[APIWorkflowDef]:
    return [api_mapper.workflow_def_to_api(workflow_def) for workflow_def in workflow_def_service.list(session=session)]

@app.get(
    "/workflow_defs/{workflow_def_id}",
    tags = ["WorkflowDef"],
    summary="Get a specific workflow definition by id",
    description = "Get a specific workflow definition by id"
)
async def workflow_def_get(workflow_def_id:str, session: Session = Depends(get_db)) -> APIWorkflowDef:
    workflow_def = workflow_def_service.get_workflow_def(workflow_def_id, session=session)
    if workflow_def is None:
        raise HTTPException(status_code=404)
    return api_mapper.workflow_def_to_api(workflow_def)

@app.post(
    "/workflow_defs",
    status_code=201,
    tags = ["WorkflowDef"],
    summary="Create a workflow definition",
    description = "Create a workflow definition"
)
async def task_def_create(create_workflow_def_details:APICreateWorkflowDefDetails, session: Session = Depends(get_db)) -> APIWorkflowDef:
    try:
        return api_mapper.workflow_def_to_api(
            workflow_def_service.create_workflow_def(
                api_mapper.create_workflow_def_details_to_model(create_workflow_def_details), session=session
            )
        )
    except core_exceptions.BadInput as e:
        raise HTTPException(status_code=400, detail=str(e))


#############################################################
# Task Def APIs
#############################################################
@app.get(
    "/task_defs",
    tags = ["TaskDef"],
    summary="List all task definitions",
    description = "List all task definitions"
)
async def task_def_list(session: Session = Depends(get_db)) -> List[APITaskDef]:
    return [api_mapper.task_def_to_api(task_def) for task_def in workflow_def_service.list_tasks(session=session)]

@app.get(
    "/task_defs/{task_def_id}",
    tags = ["TaskDef"],
    summary="Get a specific task definition by id",
    description = "Get a specific task definition by id"
)
async def task_def_get(task_def_id:str, session: Session = Depends(get_db)) -> APITaskDef:
    task_def = workflow_def_service.get_task_def(task_def_id, session=session)
    if task_def is None:
        raise HTTPException(status_code=404)
    return api_mapper.task_def_to_api(task_def)
        

@app.post(
    "/task_defs",
    status_code=201,
    tags = ["TaskDef"],
    summary="Create a task definition",
    description = "Create a task definition"
)
async def task_def_create(create_task_def_details:APICreateTaskDefDetails, session: Session = Depends(get_db)) -> APITaskDef:
    return api_mapper.task_def_to_api(
        workflow_def_service.create_task_def(
            api_mapper.create_task_def_details_to_model(create_task_def_details), session=session
        )
    )

#############################################################
# Schema APIs
#############################################################
@app.get(
    "/schemas",
    tags = ["Schema"],
    summary="List all schemas",
    description = "List all schemas"
)
async def schema_list(session: Session = Depends(get_db)) -> List[APISchema]:
    return [api_mapper.schema_to_api(schema) for schema in schema_service.list(session=session)]

@app.post(
    "/schemas",
    status_code=201,
    tags = ["Schema"],
    summary="Create a schema",
    description = "Create a schema"
)
async def schema_create(create_schema_details:APICreateSchemaDetails, session: Session = Depends(get_db)) -> APISchema:
    schema = await schema_service.create(
        api_mapper.create_schema_details_to_model(create_schema_details), session=session
    )
    return api_mapper.schema_to_api(schema)

@app.get(
    "/schemas/{schema_id}",
    tags = ["Schema"],
    summary="Get a specific schema by id",
    description = "Get a specific schema by id"
)
async def schema_get(schema_id:str, session: Session = Depends(get_db)) -> APISchema:
    schema = schema_service.get(schema_id, session=session)
    if schema is None:
        raise HTTPException(status_code=404)
    return api_mapper.schema_to_api(schema)
        

#############################################################
# Workflow APIs
#############################################################
@app.get(
    "/workflows",
    tags = ["Workflow"],
    summary="List all workflows",
    description = "List all workflows"
)
async def workflow_list(session: Session = Depends(get_db)) -> List[APIWorkflow]:
    return [api_mapper.workflow_to_api(workflow) for workflow in workflow_service.list(session=session)]

@app.post(
    "/workflows",
    status_code=201,
    tags = ["Workflow"],
    summary="Create a workflow",
    description = "Create a workflow"
)
async def workflow_create(create_workflow_details:APICreateWorkflowDetails, session: Session = Depends(get_db)) -> APIWorkflow:
    workflow = await workflow_service.create_workflow(
        api_mapper.create_workflow_details_to_model(create_workflow_details), session=session
    )
    return api_mapper.workflow_to_api(workflow)

@app.post(
    "/workflows/{workflow_id}/restart",
    status_code=200,
    tags = ["Workflow"],
    summary="Restart a failed workflow",
    description = "Restart a failed workflow"
)
async def restart_failed_workflow(workflow_id:str, session: Session = Depends(get_db)) -> APIWorkflow:
    try:
        workflow = await workflow_service.restart_failed_workflow(
            workflow_id, session=session
        )
        return api_mapper.workflow_to_api(workflow)
    except core_exceptions.BadInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    except core_exceptions.WorkflowNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get(
    "/workflows/{workflow_id}",
    tags = ["Workflow"],
    summary="Get a specific workflow by id",
    description = "Get a specific workflow by id"
)
async def workflow_get(workflow_id:str, session: Session = Depends(get_db)) -> APIWorkflow:
    workflow = api_mapper.workflow_to_api(workflow_service.get_workflow(workflow_id, session=session))
    if workflow is None:
        raise HTTPException(status_code=404)
    return workflow

@app.get(
    "/workflows/{workflow_id}/events",
    tags = ["Workflow"],
    summary="Get all events for a specific workflow by id",
    description = "Get all events for a specific workflow by id"
)
async def workflow_list_events(workflow_id:str, session: Session = Depends(get_db)) -> List[APIEvent]:
    return [
        api_mapper.event_to_api(event) for event in event_service.list(workflow_id, session=session)
    ] 

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/webui", StaticFiles(directory=os.path.join(PROJECT_ROOT, "webui", "dist"), html=True), name="webui")
