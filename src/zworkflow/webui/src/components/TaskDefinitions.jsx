import { useState, useEffect } from 'react'
import { getTaskDef, listTaskDefs } from '../../ZWorkflowClient'
import TaskDef from './TaskDef'

export default function TaskDefinitions() {
  const [taskDefs, setTaskDefs] = useState([])
  const [error, setError] = useState(null)
  const [selectedTaskDefId, setSelectedTaskDefId] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('taskDefId')
  })
  const [taskDefView, setTaskDefView] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('taskDefView')
  })

  useEffect(() => {
    listTaskDefs()
      .then(setTaskDefs)
      .catch(err => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedTaskDefId || taskDefView !== 'detail') return undefined

    let isMounted = true

    getTaskDef(selectedTaskDefId)
      .then(taskDef => {
        if (!isMounted) return

        setTaskDefs(currentTaskDefs => {
          const index = currentTaskDefs.findIndex(item => String(item.id) === selectedTaskDefId)
          if (index === -1) return [taskDef, ...currentTaskDefs]

          const nextTaskDefs = [...currentTaskDefs]
          nextTaskDefs[index] = taskDef
          return nextTaskDefs
        })
      })
      .catch(err => {
        if (isMounted) setError(err.message)
      })

    return () => {
      isMounted = false
    }
  }, [selectedTaskDefId, taskDefView])

  useEffect(() => {
    const handleHashChange = () => {
      const options = new URLSearchParams(window.location.hash.slice(1))
      setSelectedTaskDefId(options.get('taskDefId'))
      setTaskDefView(options.get('taskDefView'))
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
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

  const visibleTaskDefs = selectedTaskDefId
    ? taskDefs.filter(taskDef => String(taskDef.id) === selectedTaskDefId)
    : taskDefs
  const isDetailView = selectedTaskDefId && taskDefView === 'detail'

  return (
    <div>
      <div className="panel-header">
        <h2>Task Definitions</h2>
        <p>Manage and browse your task definitions.</p>
      </div>
      {selectedTaskDefId && taskDefs.length > 0 && visibleTaskDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">⚠️</div>
          <h3>Task definition not found</h3>
          <p>No task definition exists with ID {selectedTaskDefId}.</p>
        </div>
      ) : taskDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">📋</div>
          <h3>No task definitions yet</h3>
          <p>Task definitions will appear here once they are created.</p>
        </div>
      ) : isDetailView ? (
        <div className="def-list">
          {visibleTaskDefs.map(td => (
            <div key={td.id} className="def-list-item">
              <TaskDef taskDef={td} defaultExpanded={isDetailView} />
            </div>
          ))}
        </div>
      ) : (
        <table className="data-table task-def-list-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Title</th>
            </tr>
          </thead>
          <tbody>
            {visibleTaskDefs.map(td => {
              const taskDefUrl = `#${new URLSearchParams({
                activeView: 'task-definitions',
                taskDefId: td.id,
                taskDefView: 'detail',
              }).toString()}`

              return (
                <tr key={td.id}>
                  <td><a href={taskDefUrl}>{td.name}</a></td>
                  <td>v{td.version}</td>
                  <td>{td.title}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
