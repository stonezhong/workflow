class WorkflowError(Exception):
    pass

class WorkflowDefNotFound(WorkflowError):
    pass

class WorkflowNotFound(WorkflowError):
    pass

class StepDefNotFound(WorkflowError):
    pass

class TaskDefNotFound(WorkflowError):
    pass

class TaskNotFound(WorkflowError):
    pass

class SchemaNotFound(WorkflowError):
    pass

class BadInput(WorkflowError):
    pass

# 启动一个workflow的时候，给的输入参数不符合这个workflow定义指定的schema要求
class WorkflowInputSchemaViolation(WorkflowError):
    pass

# 一个workflow结束的时候，它的返回值违反了workflow定义的schema要求
class WorkflowOutputSchemaViolation(WorkflowError):
    pass

# Temporal无法启动一个Workflow
class FailedToSubmitWorkflow(WorkflowError):
    pass

# Temporal无法启动一个Task
class FailedToSubmitTask(WorkflowError):
    pass

# 创建TaskDef或WorkflowDef的时候，使用的JSON Schema不符合规范 （应该是JOSN Schma Object)
class InvalidJSONSchema(WorkflowError):
    pass