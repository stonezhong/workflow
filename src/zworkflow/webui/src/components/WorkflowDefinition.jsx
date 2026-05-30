import { useState } from 'react'
import YAML from 'yaml'
import DagView from './DagView'
import PopupPanel from './PopupPanel'
import StepDefView from './StepDefView'

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

function SchemaButton({ schema, label, onShow }) {
  const hasSchema = schema != null

  if (!hasSchema) {
    return <span className="empty-note">No schema defined.</span>
  }

  return (
    <div className="foldable-schema">
      <button
        type="button"
        className="schema-toggle icon-button json-view-button"
        aria-haspopup="dialog"
        aria-label={`Show ${label}`}
        title={`Show ${label}`}
        onClick={() => onShow({ schema, label })}
      >
        <span className="magnifier-icon" aria-hidden="true" />
      </button>
    </div>
  )
}

export default function WorkflowDefinition({ workflowDef, defaultExpanded = false }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [selectedStepDef, setSelectedStepDef] = useState(null)
  const [selectedSchema, setSelectedSchema] = useState(null)

  if (!workflowDef) return null

  const showStepDef = (event, stepDef) => {
    event.preventDefault()
    setSelectedStepDef(stepDef)
  }

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
                <td>
                  <SchemaButton
                    schema={workflowDef.input_schema}
                    label="Input Schema"
                    onShow={setSelectedSchema}
                  />
                </td>
              </tr>
              <tr>
                <td className="detail-label">Output Schema</td>
                <td>
                  <SchemaButton
                    schema={workflowDef.output_schema}
                    label="Output Schema"
                    onShow={setSelectedSchema}
                  />
                </td>
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
                    <td>
                      <a
                        href={`#step-def-${step.id}`}
                        className="step-def-link"
                        onClick={event => showStepDef(event, step)}
                      >
                        <code>{step.key}</code>
                      </a>
                    </td>
                    <td>{step.title}</td>
                    <td>{STEP_TYPE_LABEL[step.type] ?? step.type}</td>
                    <td>{stepInvokeLabel(step)}</td>
                    <td><code className="expr">{step.input}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3 className="section-subheading">Step Diagram</h3>
            <div>
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

      {selectedSchema && (
        <PopupPanel
          title={selectedSchema.label}
          className="schema-popup"
          onClose={() => setSelectedSchema(null)}
        >
          <pre className="json-block schema-block">{YAML.stringify(selectedSchema.schema)}</pre>
        </PopupPanel>
      )}

      {selectedStepDef && (
        <PopupPanel
          title="Step Definition"
          ariaLabel={`Step definition ${selectedStepDef.key}`}
          className="step-def-popup"
          onClose={() => setSelectedStepDef(null)}
        >
          <StepDefView stepDef={selectedStepDef} />
        </PopupPanel>
      )}
    </div>
  )
}
