import { useState, useEffect } from 'react'
import { getWorkflow, listWorkflows } from '../../ZWorkflowClient'
import Workflow from './Workflow'
import WorkflowSummary from './WorkflowSummary'

export default function Workflows() {
  const [workflows, setWorkflows] = useState([])
  const [error, setError] = useState(null)
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('workflowId')
  })
  const [workflowView, setWorkflowView] = useState(() => {
    const options = new URLSearchParams(window.location.hash.slice(1))
    return options.get('workflowView')
  })

  useEffect(() => {
    listWorkflows()
      .then(setWorkflows)
      .catch(err => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedWorkflowId || workflowView !== 'detail') return undefined

    let isMounted = true

    const reloadWorkflow = () => {
      getWorkflow(selectedWorkflowId)
        .then(workflow => {
          if (!isMounted) return

          setWorkflows(currentWorkflows => {
            const index = currentWorkflows.findIndex(item => String(item.id) === selectedWorkflowId)
            if (index === -1) return [workflow, ...currentWorkflows]

            const nextWorkflows = [...currentWorkflows]
            nextWorkflows[index] = workflow
            return nextWorkflows
          })
        })
        .catch(err => {
          if (isMounted) setError(err.message)
        })
    }

    reloadWorkflow()
    const intervalId = window.setInterval(reloadWorkflow, 1000)

    return () => {
      isMounted = false
      window.clearInterval(intervalId)
    }
  }, [selectedWorkflowId, workflowView])

  useEffect(() => {
    const handleHashChange = () => {
      const options = new URLSearchParams(window.location.hash.slice(1))
      setSelectedWorkflowId(options.get('workflowId'))
      setWorkflowView(options.get('workflowView'))
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  if (error) {
    return (
      <div>
        <div className="panel-header">
          <h2>Workflows</h2>
        </div>
        <div className="placeholder-card">
          <div className="icon">⚠️</div>
          <h3>Failed to load</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  const visibleWorkflows = selectedWorkflowId
    ? workflows.filter(workflow => String(workflow.id) === selectedWorkflowId)
    : workflows
  const isDetailView = selectedWorkflowId && workflowView === 'detail'

  return (
    <div>
      <div className="panel-header">
        <h2>Workflows</h2>
        <p>View and manage running and completed workflows.</p>
      </div>
      {selectedWorkflowId && workflows.length > 0 && visibleWorkflows.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">⚠️</div>
          <h3>Workflow not found</h3>
          <p>No workflow exists with ID {selectedWorkflowId}.</p>
        </div>
      ) : workflows.length === 0 ? (
        <div className="placeholder-card">
          <div className="icon">▶️</div>
          <h3>No workflows yet</h3>
          <p>Active and historical workflows will appear here.</p>
        </div>
      ) : isDetailView ? (
        <div className="def-list">
          {visibleWorkflows.map(workflow => (
            <div key={workflow.id} className="def-list-item">
              <Workflow workflow={workflow} />
            </div>
          ))}
        </div>
      ) : (
        <table className="data-table workflow-list-table">
          <thead>
            <tr>
              <th>State</th>
              <th>Title</th>
              <th>Time Created</th>
              <th>Time Started</th>
              <th>Time Ended</th>
            </tr>
          </thead>
          <tbody>
            {visibleWorkflows.map(workflow => (
              <WorkflowSummary key={workflow.id} workflow={workflow} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
