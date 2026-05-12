import { useState } from 'react'

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

export default function TaskDef({ taskDef }) {
  const [isExpanded, setIsExpanded] = useState(false)

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
              <td><FoldableSchema schema={taskDef.input_schema} /></td>
            </tr>
            <tr>
              <td className="detail-label">Output Schema</td>
              <td><FoldableSchema schema={taskDef.output_schema} /></td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  )
}
