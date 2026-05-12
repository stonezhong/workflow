import { useState, useEffect } from 'react'
import YAML from 'yaml'
import { listSchemas } from '../../ZWorkflowClient'

function SchemaDefinition({ schema }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!schema) return null

  return (
    <div className="schema-def">
      <button
        type="button"
        className="def-summary"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded(value => !value)}
      >
        <span className="def-name">{schema.name}</span>
        <span className="def-version">v{schema.version}</span>
      </button>

      {isExpanded && (
        <table className="detail-table def-details">
          <tbody>
            <tr>
              <td className="detail-label">ID</td>
              <td>{schema.id}</td>
            </tr>
            <tr>
              <td className="detail-label">Name</td>
              <td>{schema.name}</td>
            </tr>
            <tr>
              <td className="detail-label">Version</td>
              <td>{schema.version}</td>
            </tr>
            <tr>
              <td className="detail-label">Title</td>
              <td>{schema.title}</td>
            </tr>
            <tr>
              <td className="detail-label">Description</td>
              <td>{schema.description}</td>
            </tr>
            <tr>
              <td className="detail-label">Definition</td>
              <td>
                <pre className="json-block schema-block">{YAML.stringify(schema.definition)}</pre>
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  )
}

export default function Schemas() {
  const [schemas, setSchemas] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    listSchemas()
      .then(setSchemas)
      .catch(err => setError(err.message))
  }, [])

  if (error) {
    return (
      <div>
        <div className="panel-header">
          <h2>Schemas</h2>
        </div>
        <div className="placeholder-card">
          <div className="icon">⚠️</div>
          <h3>Failed to load</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="panel-header">
        <h2>Schemas</h2>
        <p>Browse all registered schemas.</p>
      </div>
      {schemas.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">{'{}'}</div>
          <h3>No schemas yet</h3>
          <p>Schemas will appear here once they are created.</p>
        </div>
      ) : (
        <div className="def-list">
          {schemas.map(schema => (
            <div key={schema.id} className="def-list-item">
              <SchemaDefinition schema={schema} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
