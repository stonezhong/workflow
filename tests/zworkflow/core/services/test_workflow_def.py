import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import create_all_tables, StepDefType, WorkflowState, TaskState
from zworkflow.core.services import WorkflowDefService, WorkflowService
from zworkflow.core.models import CreateWorkflowDefDetails, WorkflowDef, CreateTaskDefDetails, TaskDef, CreateWorkflowDefStepDetails, NameAndVersion, StepDefDepDetails
from zworkflow.core.models import CreateWorkflowDetails

def is_task_def_same(task_def1: TaskDef|None, task_def2: TaskDef|None) -> bool:
    if task_def1 is None and task_def2 is None:
        return True
    if task_def1 is None and task_def2 is not None:
        return False
    if task_def1 is not None and task_def2 is None:
        return False
    if task_def1.id != task_def2.id:
        return False
    if task_def1.name != task_def2.name:
        return False
    if task_def1.version != task_def2.version:
        return False
    if task_def1.description != task_def2.description:
        return False
    if task_def1.title != task_def2.title:
        return False
    if task_def1.input_schema != task_def2.input_schema:
        return False
    if task_def1.output_schema != task_def2.output_schema:
        return False
    return True
    
# 测试创建workflow def
def test_task_workflow_def_creation(
        engine:Engine, 
        workflow_def_service: WorkflowDefService
):
    with Session(engine) as session:
        with session.begin() as transaction:
            # 定义一个task def
            create_task_def_details = CreateTaskDefDetails(
                name = "foo-task",
                version = "1.0",
                description = "blah",
                title = "blah",
                input_schema = None,
                output_schema = None
            )
            task_def:TaskDef = workflow_def_service.create_task_def(create_task_def_details, session = session)

            # 创建一个workflow def
            create_workflow_def_details = CreateWorkflowDefDetails(
                name = "foo-workflow",
                version = "1.0",
                description = "blah",
                title = "blah",
                steps = [
                    CreateWorkflowDefStepDetails(
                        key = "step1",
                        description = "step1",
                        title = "step1",
                        type = StepDefType.TASK,
                        input = '{"x": 1, "y": 2}',
                        invoke_task_def_nv = NameAndVersion(
                            name = "foo-task", version = "1.0"
                        )
                    ),
                    CreateWorkflowDefStepDetails(
                        key = "step2",
                        description = "step2",
                        title = "step2",
                        type = StepDefType.TASK,
                        input = '{"x": 2, "y": 3}',
                        invoke_task_def_nv = NameAndVersion(
                            name = "foo-task", version = "1.0"
                        )
                    )
                ],
                step_deps = [
                    StepDefDepDetails(source_step_def_key="step1", destination_step_def_key="step2")
                ],
                input_schema = None,
                output_schema = None
            )
            workflow_def:WorkflowDef = workflow_def_service.create_workflow_def(create_workflow_def_details, session = session)
            
            # 检查task_def的正确性
            assert task_def.name == "foo-task"
            assert task_def.version == "1.0"
            assert task_def.description == "blah"
            assert task_def.title == "blah"
            assert task_def.input_schema is None
            assert task_def.output_schema is None

            # 检查workflow_def的正确性
            assert workflow_def.name == "foo-workflow"
            assert workflow_def.version == "1.0"
            assert workflow_def.description == "blah"
            assert workflow_def.title == "blah"
            assert len(workflow_def.steps) == 2
            sorted_steps = sorted(workflow_def.steps, key = lambda step: step.key)

            assert sorted_steps[0].workflow_def is workflow_def
            assert sorted_steps[0].key == "step1"
            assert sorted_steps[0].description == "step1"
            assert sorted_steps[0].title == "step1"
            assert sorted_steps[0].type == StepDefType.TASK
            assert sorted_steps[0].input == '{"x": 1, "y": 2}'
            assert is_task_def_same(sorted_steps[0].invoke_task_def, task_def)
            assert sorted_steps[0].invoke_workflow_def is None

            assert sorted_steps[1].workflow_def is workflow_def
            assert sorted_steps[1].key == "step2"
            assert sorted_steps[1].description == "step2"
            assert sorted_steps[1].title == "step2"
            assert sorted_steps[1].type == StepDefType.TASK
            assert sorted_steps[1].input == '{"x": 2, "y": 3}'
            assert is_task_def_same(sorted_steps[1].invoke_task_def, task_def)
            assert sorted_steps[1].invoke_workflow_def is None

            assert len(workflow_def.step_deps) == 1
            workflow_def.step_deps[0].workflow_def is workflow_def
            workflow_def.step_deps[0].source_step_def_key == "step1"
            workflow_def.step_deps[0].destination_step_def_key == "step2"

            assert workflow_def.input_schema is None
            assert workflow_def.output_schema is None

# 测试创建workflow
def test_task_workflow_creation(
        engine:Engine, 
        workflow_def_service: WorkflowDefService,
        workflow_service: WorkflowService
):
    with Session(engine) as session:
        with session.begin() as transaction:
            # 定义一个task def
            create_task_def_details = CreateTaskDefDetails(
                name = "foo-task",
                version = "1.0",
                description = "blah",
                title = "blah",
                input_schema = None,
                output_schema = None
            )
            task_def:TaskDef = workflow_def_service.create_task_def(create_task_def_details, session = session)

            # 创建一个workflow def
            create_workflow_def_details = CreateWorkflowDefDetails(
                name = "foo-workflow",
                version = "1.0",
                description = "blah",
                title = "blah",
                steps = [
                    CreateWorkflowDefStepDetails(
                        key = "step1",
                        description = "step1",
                        title = "step1",
                        type = StepDefType.TASK,
                        input = '{"x": 1, "y": 2}',
                        invoke_task_def_nv = NameAndVersion(
                            name = "foo-task", version = "1.0"
                        )
                    ),
                    CreateWorkflowDefStepDetails(
                        key = "step2",
                        description = "step2",
                        title = "step2",
                        type = StepDefType.TASK,
                        input = '{"x": 2, "y": 3}',
                        invoke_task_def_nv = NameAndVersion(
                            name = "foo-task", version = "1.0"
                        )
                    )
                ],
                step_deps = [
                    StepDefDepDetails(source_step_def_key="step1", destination_step_def_key="step2")
                ],
                input_schema = None,
                output_schema = None
            )
            workflow_def:WorkflowDef = workflow_def_service.create_workflow_def(create_workflow_def_details, session = session)

            # 创建一个workflow
            create_workflow_details = CreateWorkflowDetails(
                workflow_def_nv = NameAndVersion(
                    name = "foo-workflow",
                    version = "1.0"
                ),
                description = "run foo-workflow",
                title = "run foo-workflow",
                input = {"x": 1, "y": 1}
            )
            workflow = workflow_service.create_workflow_in_db(create_workflow_details, session=session)
            # 检查workflow
            assert workflow.workflow_def.name == "foo-workflow"
            assert workflow.workflow_def.version == "1.0"
            assert workflow.workflow_def.description == "blah"
            assert workflow.workflow_def.title == "blah"
            assert workflow.workflow_def.input_schema is None
            assert workflow.workflow_def.output_schema is None

            assert workflow.description == "run foo-workflow"
            assert workflow.title == "run foo-workflow"
            assert workflow.input == {"x": 1, "y": 1}
            assert workflow.state == WorkflowState.CREATED

            # we will see 2 steps            
            assert len(workflow.steps) == 2
            workflow_steps = sorted(workflow.steps, key = lambda step: step.step_def.key)
            assert workflow_steps[0].step_def.key == "step1"
            assert workflow_steps[0].step_def.description == "step1"
            assert workflow_steps[0].step_def.title == "step1"
            assert workflow_steps[0].step_def.type == StepDefType.TASK
            assert workflow_steps[0].step_def.input == '{"x": 1, "y": 2}'
            assert workflow_steps[0].step_def.invoke_task_def.name == 'foo-task'
            assert workflow_steps[0].step_def.invoke_task_def.version == '1.0'
            assert workflow_steps[0].step_def.invoke_task_def.description == 'blah'
            assert workflow_steps[0].step_def.invoke_task_def.title == 'blah'
            assert workflow_steps[0].step_def.invoke_task_def.input_schema is None
            assert workflow_steps[0].step_def.invoke_task_def.output_schema is None
            assert workflow_steps[0].step_def.invoke_workflow_def is None
            assert workflow_steps[0].invoke_task.input is None  # input will be calcuated at execute time
            assert workflow_steps[0].invoke_task.state == TaskState.CREATED
            assert workflow_steps[0].invoke_task.task_def.name == "foo-task"
            assert workflow_steps[0].invoke_task.task_def.version == "1.0"
            assert workflow_steps[0].invoke_task.task_def.description == "blah"
            assert workflow_steps[0].invoke_task.task_def.title == "blah"
            assert workflow_steps[0].invoke_task.task_def.input_schema is None
            assert workflow_steps[0].invoke_task.task_def.output_schema is None

            assert workflow_steps[1].step_def.key == "step2"
            assert workflow_steps[1].step_def.description == "step2"
            assert workflow_steps[1].step_def.title == "step2"
            assert workflow_steps[1].step_def.type == StepDefType.TASK
            assert workflow_steps[1].step_def.input == '{"x": 2, "y": 3}'
            assert workflow_steps[1].step_def.invoke_task_def.name == 'foo-task'
            assert workflow_steps[1].step_def.invoke_task_def.version == '1.0'
            assert workflow_steps[1].step_def.invoke_task_def.description == 'blah'
            assert workflow_steps[1].step_def.invoke_task_def.title == 'blah'
            assert workflow_steps[1].step_def.invoke_task_def.input_schema is None
            assert workflow_steps[1].step_def.invoke_task_def.output_schema is None
            assert workflow_steps[1].step_def.invoke_workflow_def is None
            assert workflow_steps[1].invoke_task.input is None  # input will be calcuated at execute time
            assert workflow_steps[1].invoke_task.state == TaskState.CREATED
            assert workflow_steps[1].invoke_task.task_def.name == "foo-task"
            assert workflow_steps[1].invoke_task.task_def.version == "1.0"
            assert workflow_steps[1].invoke_task.task_def.description == "blah"
            assert workflow_steps[1].invoke_task.task_def.title == "blah"
            assert workflow_steps[1].invoke_task.task_def.input_schema is None
            assert workflow_steps[1].invoke_task.task_def.output_schema is None
