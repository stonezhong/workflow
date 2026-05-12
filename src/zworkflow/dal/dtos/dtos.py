from __future__ import annotations

from typing import List
import uuid
from enum import Enum

from sqlalchemy import String, UniqueConstraint, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

######################################################################################
# 定义Workflow
######################################################################################
class WorkflowDefDTO(Base):
    __tablename__ = "workflow_def"

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_workflow_def_name_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    # name + version is unique
    name: Mapped[str]
    version: Mapped[str]
    
    description: Mapped[str]
    title: Mapped[str]
    input_schema: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)
    output_schema: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)

    steps: Mapped[List[StepDefDTO]] = relationship(
        "StepDefDTO",
        foreign_keys="[StepDefDTO.workflow_def_id]",
        back_populates="workflow_def",
        init=False
    )

    step_deps: Mapped[List[StepDefDepDTO]] = relationship(
        "StepDefDepDTO",
        foreign_keys="[StepDefDepDTO.workflow_def_id]",
        back_populates="workflow_def",
        init=False
    )

######################################################################################
# 定义Workflow中步骤的依赖关系
######################################################################################
class StepDefDepDTO(Base):
    __tablename__ = "step_def_dep"

    __table_args__ = (
        UniqueConstraint(
            "workflow_def_id", 
            "source_step_def_key", 
            "destination_step_def_key", 
            name="uq_step_def_dep_workflow_def_id_sd"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    workflow_def_id: Mapped[str] = mapped_column(ForeignKey("workflow_def.id"))
    workflow_def: Mapped[WorkflowDefDTO] = relationship(init=False)

    # dest depend on source
    source_step_def_key: Mapped[str]
    destination_step_def_key: Mapped[str]


######################################################################################
# 定义Workflow中的一个步骤
######################################################################################
class StepDefType(Enum):
    TASK = 1        # this step invoke a task
    WORKFLOW = 2    # this step invoke a workflow


class StepDefDTO(Base):
    __tablename__ = "step_def"

    __table_args__ = (
        UniqueConstraint("workflow_def_id", "key", name="uq_step_def_workflow_def_id_key"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    # 每个step def 都属于一个workflow def
    workflow_def_id: Mapped[str] = mapped_column(ForeignKey("workflow_def.id"))
    workflow_def: Mapped[WorkflowDefDTO] = relationship(foreign_keys=[workflow_def_id], init=False)

    # key is unique within the same workflow def
    key: Mapped[str]

    title: Mapped[str]
    description: Mapped[str]

    # step def的类型
    type: Mapped[StepDefType]

    # the input of a step, could be an expression
    input: Mapped[str]

    # if type is Task
    invoke_task_def_id: Mapped[str | None] = mapped_column(ForeignKey("task_def.id"), nullable=True, default=None)
    invoke_task_def: Mapped[TaskDefDTO | None] = relationship(foreign_keys="[StepDefDTO.invoke_task_def_id]", init=False)

    # if type is  Workflow
    invoke_workflow_def_id: Mapped[str | None] = mapped_column(ForeignKey("workflow_def.id"), nullable=True, default=None)
    invoke_workflow_def: Mapped[WorkflowDefDTO | None] = relationship(foreign_keys="[StepDefDTO.invoke_workflow_def_id]", init=False)

class WorkflowState(Enum):
    CREATED         = 1
    RUN_REQUESTED   = 2
    RUNNING         = 3
    SUCCEEDED       = 4
    FAILED          = 5

######################################################################################
# 代表workflow的一次执行
######################################################################################

class WorkflowDTO(Base):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    # 每个workflow都是workflow def的一个instance
    workflow_def_id: Mapped[str] = mapped_column(ForeignKey("workflow_def.id"))
    workflow_def: Mapped[WorkflowDefDTO] = relationship(init=False)
   
    description: Mapped[str]
    title: Mapped[str]

    state: Mapped[WorkflowState]
    input: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)
    output: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)

    steps: Mapped[List[StepDTO]] = relationship(
        "StepDTO",
        foreign_keys="[StepDTO.workflow_id]",
        back_populates="workflow",
        init=False
    )

######################################################################################
# 代表workflow中的一个步骤的执行
######################################################################################

class StepDTO(Base):
    __tablename__ = "step"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    # 每个step 都属于一个workflow
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow.id"))
    workflow: Mapped[WorkflowDTO] = relationship(foreign_keys=[workflow_id], init=False)

    step_def_id: Mapped[str] = mapped_column(ForeignKey("step_def.id"))
    step_def: Mapped[StepDefDTO] = relationship(foreign_keys=[step_def_id], init=False)

    # if type is Task
    invoke_task_id: Mapped[str | None] = mapped_column(ForeignKey("task.id"), nullable=True, default=None)
    invoke_task: Mapped[TaskDTO | None] = relationship(foreign_keys="[StepDTO.invoke_task_id]", init=False)

    # if type is  Workflow
    invoke_workflow_id: Mapped[str | None] = mapped_column(ForeignKey("workflow.id"), nullable=True, default=None)
    invoke_workflow: Mapped[WorkflowDTO | None] = relationship(foreign_keys="[StepDTO.invoke_workflow_id]", init=False)

######################################################################################
# 代表一个task的执行
######################################################################################

class TaskState(Enum):
    CREATED         = 1     # 刚刚被创建，还未被执行
    RUN_REQUESTED   = 2     # 已经通知temporal执行这个步骤
    RUNNING         = 3     # 正在被执行
    SUCCEEDED       = 4     # 成功完成了
    FAILED          = 5     # 失败了

class TaskDTO(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )    

    # Task都是从属于一个workflow
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow.id"))
    workflow: Mapped[WorkflowDTO] = relationship(init=False)

    # Task都是TaskDef的一个instance
    task_def_id: Mapped[str] = mapped_column(ForeignKey("task_def.id"))
    task_def: Mapped[TaskDefDTO] = relationship(init=False)

    state: Mapped[TaskState]
    input: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)
    output: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)

######################################################################################
# 定义一个Task
######################################################################################

class TaskDefDTO(Base):
    __tablename__ = "task_def"

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_task_def_name_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    # name + version is unique
    name: Mapped[str]
    version: Mapped[str]

    description: Mapped[str]
    title: Mapped[str]

    input_schema: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)
    output_schema: Mapped[dict|None] = mapped_column(JSON, nullable=True, default=None)

######################################################################################
# 代表一个schema
######################################################################################

class SchemaDTO(Base):
    __tablename__ = "schema"

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_schema_name_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        insert_default=lambda: str(uuid.uuid4()),
        init=False
    )

    name: Mapped[str]
    version: Mapped[str]

    description: Mapped[str]
    title: Mapped[str]

    definition: Mapped[dict] = mapped_column(JSON)
