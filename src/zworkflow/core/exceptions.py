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