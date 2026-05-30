const STEP_TYPE_LABEL = { 1: 'Task', 2: 'Workflow' }

function emptyValue(value) {
  return value === undefined || value === null || value === ''
}

function Value({ value }) {
  if (emptyValue(value)) {
    return <span className="empty-note">No value defined.</span>
  }

  return value
}

function invokeLabel(stepDef) {
  if (stepDef.invoke_task_def) {
    const taskDef = stepDef.invoke_task_def
    return `${taskDef.name} v${taskDef.version}`
  }
  if (stepDef.invoke_workflow_def) {
    const workflowDef = stepDef.invoke_workflow_def
    return `${workflowDef.name} v${workflowDef.version}`
  }
  return null
}

export default function StepDefView({ stepDef }) {
  if (!stepDef) return null

  const typeLabel = STEP_TYPE_LABEL[stepDef.type] ?? stepDef.type
  const invokedLabel = invokeLabel(stepDef)
  const invokedTaskDef = stepDef.invoke_task_def
  const invokedWorkflowDef = stepDef.invoke_workflow_def
  const invokedTaskDefUrl = invokedTaskDef
    ? `#${new URLSearchParams({
      activeView: 'task-definitions',
      taskDefId: invokedTaskDef.id,
      taskDefView: 'detail',
    }).toString()}`
    : null
  const invokedWorkflowDefUrl = invokedWorkflowDef
    ? `#${new URLSearchParams({
      activeView: 'workflow-definitions',
      workflowDefId: invokedWorkflowDef.id,
      workflowDefView: 'detail',
    }).toString()}`
    : null

  return (
    <div className="step-def-view">
      <div className="def-summary">
        <span className="def-name">{stepDef.title || stepDef.key}</span>
        <span className="def-version">{typeLabel}</span>
      </div>

      <table className="detail-table def-details">
        <tbody>
          <tr>
            <td className="detail-label">Key</td>
            <td><code>{stepDef.key}</code></td>
          </tr>
          <tr>
            <td className="detail-label">Title</td>
            <td><Value value={stepDef.title} /></td>
          </tr>
          <tr>
            <td className="detail-label">Description</td>
            <td><Value value={stepDef.description} /></td>
          </tr>
          <tr>
            <td className="detail-label">Type</td>
            <td>{typeLabel}</td>
          </tr>
          <tr>
            <td className="detail-label">Invokes</td>
            <td>
              {invokedTaskDef ? (
                <a
                  href={invokedTaskDefUrl}
                  className="step-def-link"
                >
                  {invokedLabel}
                </a>
              ) : invokedWorkflowDef ? (
                <a
                  href={invokedWorkflowDefUrl}
                  className="step-def-link"
                >
                  {invokedLabel}
                </a>
              ) : (
                <Value value={invokedLabel} />
              )}
            </td>
          </tr>
          <tr>
            <td className="detail-label">Input</td>
            <td>
              {emptyValue(stepDef.input) ? (
                <span className="empty-note">No input expression defined.</span>
              ) : (
                <code className="expr">{stepDef.input}</code>
              )}
            </td>
          </tr>
          <tr>
            <td className="detail-label">Return</td>
            <td>
              <span
                className={stepDef.is_return_step ? 'status-icon status-icon-true' : 'status-icon status-icon-false'}
                aria-label={stepDef.is_return_step ? 'Return true' : 'Return false'}
                role="img"
              >
                {stepDef.is_return_step ? '✅' : '❌'}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
