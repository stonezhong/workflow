import { useState, useEffect } from 'react'
import { listTaskDefs } from '../../ZWorkflowClient'
import TaskDef from './TaskDef'

export default function TaskDefinitions() {
  const [taskDefs, setTaskDefs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    listTaskDefs()
      .then(setTaskDefs)
      .catch(err => setError(err.message))
  }, [])

  if (error) {
    return (
      <div>
        <div className="panel-header">
          <h2>Task Definitions</h2>
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
        <h2>Task Definitions</h2>
        <p>Manage and browse your task definitions.</p>
      </div>
      {taskDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">📋</div>
          <h3>No task definitions yet</h3>
          <p>Task definitions will appear here once they are created.</p>
        </div>
      ) : (
        <div className="def-list">
          {taskDefs.map(td => (
            <div key={td.id} className="def-list-item">
              <TaskDef taskDef={td} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
