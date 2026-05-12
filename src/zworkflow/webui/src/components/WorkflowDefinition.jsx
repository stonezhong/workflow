import { useState } from 'react'
import DagView from './DagView'

const STEP_TYPE_LABEL = { 1: 'Task', 2: 'Workflow' }

function stepInvokeLabel(step) {
  if (step.invoke_task_def) {
    const t = step.invoke_task_def
    return `${t.name} v${t.version}`
  }
  if (step.invoke_workflow_def) {
    const w = step.invoke_workflow_def
    return `${w.name} v${w.version}`
  }
  return '—'
}

function FoldableSchema({ schema }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const hasSchema = schema != null

  if (!hasSchema) {
    return <span className="empty-note">No schema defined.</span>
  }

  return (
    <div className="foldable-schema">
      <button
        type="button"
        className="schema-toggle"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded(value => !value)}
      >
        {isExpanded ? 'Hide schema' : 'Show schema'}
      </button>
      {isExpanded && (
        <pre className="json-block schema-block">{JSON.stringify(schema, null, 2)}</pre>
      )}
    </div>
  )
}

export default function WorkflowDefinition({ workflowDef }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!workflowDef) return null

  return (
    <div className="wf-def">
      <button
        type="button"
        className="wf-def-summary"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded(value => !value)}
      >
        <span className="wf-def-name">{workflowDef.name}</span>
        <span className="wf-def-version">v{workflowDef.version}</span>
      </button>

      {isExpanded && (
        <>
          <table className="detail-table wf-def-details">
            <tbody>
              <tr>
                <td className="detail-label">ID</td>
                <td>{workflowDef.id}</td>
              </tr>
              <tr>
                <td className="detail-label">Name</td>
                <td>{workflowDef.name}</td>
              </tr>
              <tr>
                <td className="detail-label">Version</td>
                <td>{workflowDef.version}</td>
              </tr>
              <tr>
                <td className="detail-label">Title</td>
                <td>{workflowDef.title}</td>
              </tr>
              <tr>
                <td className="detail-label">Description</td>
                <td>{workflowDef.description}</td>
              </tr>
              <tr>
                <td className="detail-label">Input Schema</td>
                <td><FoldableSchema schema={workflowDef.input_schema} /></td>
              </tr>
              <tr>
                <td className="detail-label">Output Schema</td>
                <td><FoldableSchema schema={workflowDef.output_schema} /></td>
              </tr>
            </tbody>
          </table>

          <h3 className="section-subheading">Steps</h3>
          {workflowDef.steps.length === 0 ? (
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
                </tr>
              </thead>
              <tbody>
                {workflowDef.steps.map(step => (
                  <tr key={step.id}>
                    <td><code>{step.key}</code></td>
                    <td>{step.title}</td>
                    <td>{STEP_TYPE_LABEL[step.type] ?? step.type}</td>
                    <td>{stepInvokeLabel(step)}</td>
                    <td><code className="expr">{step.input}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3 className="section-subheading">Step Dependencies</h3>
            <div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                  </tr>
                </thead>
                <tbody>
                  {workflowDef.step_deps.map(dep => (
                    <tr key={dep.id}>
                      <td><code>{dep.source_step_def_key}</code></td>
                      <td><code>{dep.destination_step_def_key}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <DagView
                nodes={workflowDef.steps.map(step => ({
                  key: step.key,
                  title: step.title,
                  color: '#f8fafc',
                }))}
                connections={ workflowDef.step_deps.map(dep => ({source: dep.source_step_def_key, destination: dep.destination_step_def_key}) )}
              />
            </div>
        </>
      )}
    </div>
  )
}
