import { useState, useEffect } from 'react'
import { getWorkflowDef, listWorkflowDefs } from '../../ZWorkflowClient'
import WorkflowDefinition from './WorkflowDefinition'

export default function WorkflowDefinitions() {
  const [workflowDefs, setWorkflowDefs] = useState([])
  const [error, setError] = useState(null)
  const [selectedWorkflowDefId, setSelectedWorkflowDefId] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('workflowDefId')
  })
  const [workflowDefView, setWorkflowDefView] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('workflowDefView')
  })

  useEffect(() => {
    listWorkflowDefs()
      .then(setWorkflowDefs)
      .catch(err => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedWorkflowDefId || workflowDefView !== 'detail') return undefined

    let isMounted = true

    getWorkflowDef(selectedWorkflowDefId)
      .then(workflowDef => {
        if (!isMounted) return

        setWorkflowDefs(currentWorkflowDefs => {
          const index = currentWorkflowDefs.findIndex(item => String(item.id) === selectedWorkflowDefId)
          if (index === -1) return [workflowDef, ...currentWorkflowDefs]

          const nextWorkflowDefs = [...currentWorkflowDefs]
          nextWorkflowDefs[index] = workflowDef
          return nextWorkflowDefs
        })
      })
      .catch(err => {
        if (isMounted) setError(err.message)
      })

    return () => {
      isMounted = false
    }
  }, [selectedWorkflowDefId, workflowDefView])

  useEffect(() => {
    const handleHashChange = () => {
      const options = new URLSearchParams(window.location.hash.slice(1))
      setSelectedWorkflowDefId(options.get('workflowDefId'))
      setWorkflowDefView(options.get('workflowDefView'))
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
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

  const visibleWorkflowDefs = selectedWorkflowDefId
    ? workflowDefs.filter(workflowDef => String(workflowDef.id) === selectedWorkflowDefId)
    : workflowDefs
  const isDetailView = selectedWorkflowDefId && workflowDefView === 'detail'

  return (
    <div>
      <div className="panel-header">
        <h2>Workflow Definitions</h2>
        <p>Manage and browse your workflow definitions.</p>
      </div>
      {selectedWorkflowDefId && workflowDefs.length > 0 && visibleWorkflowDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">⚠️</div>
          <h3>Workflow definition not found</h3>
          <p>No workflow definition exists with ID {selectedWorkflowDefId}.</p>
        </div>
      ) : workflowDefs.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">⚙️</div>
          <h3>No workflow definitions yet</h3>
          <p>Workflow definitions will appear here once they are created.</p>
        </div>
      ) : isDetailView ? (
        <div className="def-list">
          {visibleWorkflowDefs.map(wd => (
            <div key={wd.id} className="def-list-item">
              <WorkflowDefinition workflowDef={wd} defaultExpanded={isDetailView} />
            </div>
          ))}
        </div>
      ) : (
        <table className="data-table workflow-def-list-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Title</th>
            </tr>
          </thead>
          <tbody>
            {visibleWorkflowDefs.map(wd => {
              const workflowDefUrl = `#${new URLSearchParams({
                activeView: 'workflow-definitions',
                workflowDefId: wd.id,
                workflowDefView: 'detail',
              }).toString()}`

              return (
                <tr key={wd.id}>
                  <td><a href={workflowDefUrl}>{wd.name}</a></td>
                  <td>v{wd.version}</td>
                  <td>{wd.title}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
