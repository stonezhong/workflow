import DagView from './DagView'

export const STATE_LABEL = { 
    1: 'Created', 
    2: 'run requested',
    3: 'running',
    4: "succeeded",
    5: "failed"
}
export const STATE_COLOR = { 
    1: '#505050', 
    2: '#505050', 
    3: '#00ff00',
    4: '#007700',
    5: '#ff0000'
}
const STEP_TYPE_LABEL = { 1: 'Task', 2: 'Workflow' }

function stepInvokeLabel(step) {
  const stepDef = step.step_def ?? step

  if (step.invoke_task?.task_def) {
    const taskDef = step.invoke_task.task_def
    return `${taskDef.name} v${taskDef.version}`
  }
  if (step.invoke_workflow?.workflow_def) {
    const workflowDef = step.invoke_workflow.workflow_def
    return `${workflowDef.name} v${workflowDef.version}`
  }
  if (stepDef.invoke_task_def) {
    const taskDef = stepDef.invoke_task_def
    return `${taskDef.name} v${taskDef.version}`
  }
  if (stepDef.invoke_workflow_def) {
    const workflowDef = stepDef.invoke_workflow_def
    return `${workflowDef.name} v${workflowDef.version}`
  }
  return '—'
}

function getStepInput(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? JSON.stringify(step.invoke_task.input, null, 2) : "";
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? JSON.stringify(step.invoke_workflow.input, null, 2) : "";
    }
    return "";
}

function getStepOutput(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? JSON.stringify(step.invoke_task.output, null, 2) : "";
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? JSON.stringify(step.invoke_workflow.output, null, 2) : "";
    }
    return "";
}

function getStepState(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.state : null;
    }
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.state : null;
    }
    return null;
}

export default function Workflow({ workflow }) {
  if (!workflow) return null

  const stateLabel = STATE_LABEL[workflow.state] ?? workflow.state
  const stateColor = STATE_COLOR[workflow.state] ?? '#64748b'
  const steps = workflow.steps ?? []
  const stepDeps = workflow.workflow_def?.step_deps ?? []
  const dagNodes = steps.map(step => {
    const state = getStepState(step)

    return {
      key: step.step_def.key,
      title: step.step_def.title,
      color: STATE_COLOR[state] ?? '#f8fafc',
    }
  })
  return (
    <div className="workflow">
      <div className="def-summary">
        <span className="def-name">
          {workflow.title}
        </span>
        <span className="state-badge" style={{ background: stateColor }}>
          {stateLabel}
        </span>
      </div>

      <table className="detail-table def-details">
        <tbody>
          <tr>
            <td className="detail-label">ID</td>
            <td>{workflow.id}</td>
          </tr>
          <tr>
            <td className="detail-label">Title</td>
            <td>{workflow.title}</td>
          </tr>
          <tr>
            <td className="detail-label">Description</td>
            <td>{workflow.description}</td>
          </tr>
          <tr>
            <td className="detail-label">State</td>
            <td>
              <span className="state-badge" style={{ background: stateColor }}>
                {stateLabel}
              </span>
            </td>
          </tr>
          <tr>
            <td className="detail-label">Workflow Def</td>
            <td>{workflow.workflow_def?.name} v{workflow.workflow_def?.version}</td>
          </tr>
          {workflow.input && (
            <tr>
              <td className="detail-label">Input</td>
              <td>
                <pre className="json-block">{JSON.stringify(workflow.input, null, 2)}</pre>
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h3 className="section-subheading">Steps</h3>
      {steps.length === 0 ? (
        <p className="empty-note">No steps defined.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Title</th>
              <th>Type</th>
              <th>Invokes</th>
              <th>Input</th>
              <th>Output</th>
            </tr>
          </thead>
          <tbody>
            {steps.map(step => {
              const stepDef = step.step_def;

              return (
              <tr key={step.id}>
                <td><code>{stepDef.key}</code></td>
                <td>{stepDef.title}</td>
                <td>{STEP_TYPE_LABEL[stepDef.type]}</td>
                <td>{stepInvokeLabel(step)}</td>
                <td><pre>{getStepInput(step)}</pre></td>
                <td><pre>{getStepOutput(step)}</pre></td>
              </tr>
              )
            })}
          </tbody>
        </table>
      )}

      <h3 className="section-subheading">Step Dependencies</h3>
      <div>
        <DagView
          nodes={dagNodes}
          connections={stepDeps.map(dep => ({source: dep.source_step_def_key, destination: dep.destination_step_def_key}))}
        />
      </div>
    </div>
  )
}
