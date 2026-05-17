import { useState } from 'react'
import PopupPanel from './PopupPanel'

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

export default function TaskDef({ taskDef, defaultExpanded = false }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [selectedSchema, setSelectedSchema] = useState(null)

  if (!taskDef) return null

  return (
    <div className="task-def">
      <button
        type="button"
        className="task-def-summary"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded(value => !value)}
      >
        <span className="task-def-name">{taskDef.name}</span>
        <span className="task-def-version">v{taskDef.version}</span>
      </button>

      {isExpanded && (
        <table className="detail-table task-def-details">
          <tbody>
            <tr>
              <td className="detail-label">ID</td>
              <td>{taskDef.id}</td>
            </tr>
            <tr>
              <td className="detail-label">Name</td>
              <td>{taskDef.name}</td>
            </tr>
            <tr>
              <td className="detail-label">Version</td>
              <td>{taskDef.version}</td>
            </tr>
            <tr>
              <td className="detail-label">Title</td>
              <td>{taskDef.title}</td>
            </tr>
            <tr>
              <td className="detail-label">Description</td>
              <td>{taskDef.description}</td>
            </tr>
            <tr>
              <td className="detail-label">Input Schema</td>
              <td>
                <SchemaButton
                  schema={taskDef.input_schema}
                  label="Input Schema"
                  onShow={setSelectedSchema}
                />
              </td>
            </tr>
            <tr>
              <td className="detail-label">Output Schema</td>
              <td>
                <SchemaButton
                  schema={taskDef.output_schema}
                  label="Output Schema"
                  onShow={setSelectedSchema}
                />
              </td>
            </tr>
          </tbody>
        </table>
      )}

      {selectedSchema && (
        <PopupPanel
          title={selectedSchema.label}
          className="schema-popup"
          onClose={() => setSelectedSchema(null)}
        >
          <pre className="json-block schema-block">{JSON.stringify(selectedSchema.schema, null, 2)}</pre>
        </PopupPanel>
      )}
    </div>
  )
}
