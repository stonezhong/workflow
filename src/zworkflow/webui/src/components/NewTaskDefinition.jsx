import { useState } from 'react'
import YAML from 'yaml'
import { createTaskDef } from '../../ZWorkflowClient'

function parseOptionalYaml(value, label) {
  const trimmedValue = value.trim()
  if (!trimmedValue) return { value: null }

  try {
    return { value: YAML.parse(trimmedValue) }
  } catch (err) {
    return { error: `Invalid ${label} YAML: ${err.message}` }
  }
}

export default function NewTaskDefinition() {
  const [name, setName] = useState('')
  const [version, setVersion] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [inputSchemaText, setInputSchemaText] = useState('')
  const [outputSchemaText, setOutputSchemaText] = useState('')
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = event => {
    event.preventDefault()
    setError(null)

    const inputSchema = parseOptionalYaml(inputSchemaText, 'input schema')
    if (inputSchema.error) {
      setError(inputSchema.error)
      return
    }

    const outputSchema = parseOptionalYaml(outputSchemaText, 'output schema')
    if (outputSchema.error) {
      setError(outputSchema.error)
      return
    }

    setIsSubmitting(true)
    createTaskDef({
      name: name.trim(),
      version: version.trim(),
      title: title.trim(),
      description,
      input_schema: inputSchema.value,
      output_schema: outputSchema.value,
    })
      .then(() => {
        window.location.hash = new URLSearchParams({
          activeView: 'task-definitions',
        }).toString()
      })
      .catch(err => setError(err.message))
      .finally(() => setIsSubmitting(false))
  }

  return (
    <div>
      <div className="panel-header">
        <h2>New Task Definition</h2>
        <p>Create a reusable task definition.</p>
      </div>

      <form className="form-panel" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}

        <div className="form-grid three-columns">
          <label className="form-field">
            <span>Name</span>
            <input
              type="text"
              value={name}
              onChange={event => setName(event.target.value)}
              required
            />
          </label>

          <label className="form-field">
            <span>Version</span>
            <input
              type="text"
              value={version}
              onChange={event => setVersion(event.target.value)}
              required
            />
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
        </div>

        <label className="form-field">
          <span>Description</span>
          <textarea
            value={description}
            onChange={event => setDescription(event.target.value)}
            rows={8}
            required
          />
        </label>

        <div className="form-grid two-columns">
          <label className="form-field">
            <span>Input Schema YAML</span>
            <textarea
              className="code-textarea"
              value={inputSchemaText}
              onChange={event => setInputSchemaText(event.target.value)}
              rows={10}
              spellCheck="false"
            />
          </label>

          <label className="form-field">
            <span>Output Schema YAML</span>
            <textarea
              className="code-textarea"
              value={outputSchemaText}
              onChange={event => setOutputSchemaText(event.target.value)}
              rows={10}
              spellCheck="false"
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Task Definition'}
          </button>
        </div>
      </form>
    </div>
  )
}
