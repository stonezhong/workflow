import { useEffect, useState } from 'react'
import { createWorkflow, listWorkflowDefs } from '../../ZWorkflowClient'

export default function NewWorkflow() {
  const [workflowDefs, setWorkflowDefs] = useState([])
  const [workflowDefId, setWorkflowDefId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [inputText, setInputText] = useState('{}')
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    listWorkflowDefs()
      .then(defs => {
        setWorkflowDefs(defs)
        setWorkflowDefId(defs[0]?.id ?? '')
      })
      .catch(err => setError(err.message))
  }, [])

  const handleSubmit = event => {
    event.preventDefault()
    setError(null)

    let input = null
    const trimmedInput = inputText.trim()
    if (trimmedInput) {
      try {
        input = JSON.parse(trimmedInput)
      } catch (err) {
        setError(`Invalid input JSON: ${err.message}`)
        return
      }
    }

    const workflowDef = workflowDefs.find(item => item.id === workflowDefId)
    if (!workflowDef) {
      setError('Select a workflow definition.')
      return
    }

    setIsSubmitting(true)
    createWorkflow({
      workflow_def_id: workflowDefId,
      workflow_def_nv: {
        name: workflowDef.name,
        version: workflowDef.version,
      },
      title,
      description,
      input,
    })
      .then(workflow => {
        window.location.hash = new URLSearchParams({
          activeView: 'workflows',
          workflowId: workflow.id,
          workflowView: 'detail',
        }).toString()
      })
      .catch(err => setError(err.message))
      .finally(() => setIsSubmitting(false))
  }

  return (
    <div>
      <div className="panel-header">
        <h2>New Workflow</h2>
        <p>Create a workflow from an existing workflow definition.</p>
      </div>

      <form className="form-panel" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}

        <label className="form-field">
          <span>Workflow Definition</span>
          <select
            value={workflowDefId}
            onChange={event => setWorkflowDefId(event.target.value)}
            required
          >
            {workflowDefs.map(workflowDef => (
              <option key={workflowDef.id} value={workflowDef.id}>
                {workflowDef.name} v{workflowDef.version}
              </option>
            ))}
          </select>
        </label>

        <label className="form-field">
          <span>Title</span>
          <input
            type="text"
            value={title}
            onChange={event => setTitle(event.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span>Description</span>
          <textarea
            value={description}
            onChange={event => setDescription(event.target.value)}
            rows={3}
            required
          />
        </label>

        <label className="form-field">
          <span>Input</span>
          <textarea
            value={inputText}
            onChange={event => setInputText(event.target.value)}
            rows={8}
            spellCheck="false"
          />
        </label>

        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={isSubmitting || workflowDefs.length === 0}>
            {isSubmitting ? 'Creating...' : 'Create Workflow'}
          </button>
        </div>
      </form>
    </div>
  )
}
