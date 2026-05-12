import { useState, useEffect } from 'react'
import { listWorkflowDefs, getWorkflowDef, createWorkflowDef } from '../../ZWorkflowClient'
import WorkflowDefinition from './WorkflowDefinition'

export default function WorkflowDefinitions() {
  const [workflowDefs, setWorkflowDefs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    listWorkflowDefs()
      .then(setWorkflowDefs)
      .catch(err => setError(err.message))
  }, [])

  if (error) {
    return (
      <div>
        <div className="panel-header">
          <h2>Workflow Definitions</h2>
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
        <h2>Workflow Definitions</h2>
        <p>Manage and browse your workflow definitions.</p>
      </div>
      {workflowDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">⚙️</div>
          <h3>No workflow definitions yet</h3>
          <p>Workflow definitions will appear here once they are created.</p>
        </div>
      ) : (
        <div className="def-list">
          {workflowDefs.map(wd => (
            <div key={wd.id} className="def-list-item">
              <WorkflowDefinition workflowDef={wd} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
