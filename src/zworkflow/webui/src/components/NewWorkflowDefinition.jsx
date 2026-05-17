import { useEffect, useState } from 'react'
import { createWorkflowDef, listTaskDefs, listWorkflowDefs } from '../../ZWorkflowClient'

const STEP_TYPES = [
  { label: 'TASK', value: 1 },
  { label: 'WORKFLOW', value: 2 },
]

function createEmptyStep() {
  return {
    key: '',
    description: '',
    title: '',
    type: 1,
    input: '',
    task_def_id: '',
    workflow_def_id: '',
    is_return_step: false,
  }
}

function createEmptyStepDep() {
  return {
    source_step_def_key: '',
    destination_step_def_key: '',
  }
}

function isStepReady(step) {
  const hasBaseFields = step.key.trim()
    && step.description.trim()
    && step.title.trim()
    && step.input.trim()

  if (step.type === 1) {
    return hasBaseFields && step.task_def_id
  }

  return hasBaseFields && step.workflow_def_id
}

function isStepEmpty(step) {
  return !step.key.trim()
    && !step.description.trim()
    && !step.title.trim()
    && !step.input.trim()
    && !step.task_def_id
    && !step.workflow_def_id
    && !step.is_return_step
}

export default function NewWorkflowDefinition() {
  const [name, setName] = useState('')
  const [version, setVersion] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [steps, setSteps] = useState([createEmptyStep()])
  const [stepDeps, setStepDeps] = useState([])
  const [workflowDefs, setWorkflowDefs] = useState([])
  const [taskDefs, setTaskDefs] = useState([])
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    Promise.all([listWorkflowDefs(), listTaskDefs()])
      .then(([nextWorkflowDefs, nextTaskDefs]) => {
        setWorkflowDefs(nextWorkflowDefs)
        setTaskDefs(nextTaskDefs)
      })
      .catch(err => setError(err.message))
  }, [])

  const updateStep = (index, field, value) => {
    setSteps(currentSteps => currentSteps.map((step, stepIndex) => (
      stepIndex === index ? { ...step, [field]: value } : step
    )))
  }

  const addStep = () => {
    const draftStep = steps[steps.length - 1]

    if (!isStepReady(draftStep)) {
      setError('Complete the highlighted step before adding it.')
      return
    }

    setError(null)
    setSteps(currentSteps => [...currentSteps, createEmptyStep()])
  }

  const removeStep = index => {
    setSteps(currentSteps => currentSteps.filter((_, stepIndex) => stepIndex !== index))
  }

  const updateStepDep = (index, field, value) => {
    setStepDeps(currentStepDeps => currentStepDeps.map((stepDep, stepDepIndex) => (
      stepDepIndex === index ? { ...stepDep, [field]: value } : stepDep
    )))
  }

  const addStepDep = () => {
    setStepDeps(currentStepDeps => [...currentStepDeps, createEmptyStepDep()])
  }

  const removeStepDep = index => {
    setStepDeps(currentStepDeps => currentStepDeps.filter((_, stepDepIndex) => stepDepIndex !== index))
  }

  const buildWorkflowDefDetails = () => {
    const addedSteps = steps.slice(0, -1)
    const draftStep = steps[steps.length - 1]
    const stepKeys = new Set(addedSteps.map(step => step.key.trim()))

    if (!isStepEmpty(draftStep)) {
      return {
        error: 'Click Add Step to include the highlighted step before creating the workflow definition.',
      }
    }

    for (const stepDep of stepDeps) {
      if (
        !stepKeys.has(stepDep.source_step_def_key)
        || !stepKeys.has(stepDep.destination_step_def_key)
      ) {
        return { error: 'Each step dependency must reference added steps.' }
      }
    }

    const apiSteps = []
    for (const step of addedSteps) {
      const stepDetails = {
        key: step.key.trim(),
        description: step.description,
        title: step.title.trim(),
        type: step.type,
        input: step.input,
        is_return_step: step.is_return_step,
      }

      if (step.type === 1) {
        const taskDef = taskDefs.find(item => item.id === step.task_def_id)
        if (!taskDef) {
          return { error: `Select a valid task definition for step "${step.key}".` }
        }

        apiSteps.push({
          ...stepDetails,
          invoke_task_def_nv: {
            name: taskDef.name,
            version: taskDef.version,
          },
        })
        continue
      }

      const workflowDef = workflowDefs.find(item => item.id === step.workflow_def_id)
      if (!workflowDef) {
        return { error: `Select a valid workflow definition for step "${step.key}".` }
      }

      apiSteps.push({
        ...stepDetails,
        invoke_workflow_def_nv: {
          name: workflowDef.name,
          version: workflowDef.version,
        },
      })
    }

    return {
      details: {
        name: name.trim(),
        version: version.trim(),
        description,
        title: title.trim(),
        steps: apiSteps,
        step_deps: stepDeps.map(stepDep => ({
          source_step_def_key: stepDep.source_step_def_key,
          destination_step_def_key: stepDep.destination_step_def_key,
        })),
        input_schema: null,
        output_schema: null,
      },
    }
  }

  const handleSubmit = event => {
    event.preventDefault()
    setError(null)

    const { details, error: detailsError } = buildWorkflowDefDetails()
    if (detailsError) {
      setError(detailsError)
      return
    }

    setIsSubmitting(true)
    createWorkflowDef(details)
      .then(() => {
        window.location.hash = new URLSearchParams({
          activeView: 'workflow-definitions',
        }).toString()
      })
      .catch(err => setError(err.message))
      .finally(() => setIsSubmitting(false))
  }

  return (
    <div>
      <div className="panel-header">
        <h2>New Workflow Definition</h2>
        <p>Create a workflow definition from structured fields.</p>
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

        <section className="form-section">
          <div className="form-section-header">
            <h3>Steps</h3>
          </div>

          <div className="step-list">
            {steps.map((step, index) => {
              const isDraftStep = index === steps.length - 1

              return (
                <div
                  className={`step-editor${isDraftStep ? ' next-step-editor' : ''}`}
                  key={index}
                >
                {!isDraftStep && (
                  <div className="step-editor-header">
                    <span />
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => removeStep(index)}
                    >
                      Remove
                    </button>
                  </div>
                )}

                <div className="form-grid step-fields-grid">
                  <label className="form-field">
                    <span>Key</span>
                    <input
                      type="text"
                      value={step.key}
                      onChange={event => updateStep(index, 'key', event.target.value)}
                      required={!isDraftStep}
                    />
                  </label>

                  <label className="form-field">
                    <span>Title</span>
                    <input
                      type="text"
                      value={step.title}
                      onChange={event => updateStep(index, 'title', event.target.value)}
                      required={!isDraftStep}
                    />
                  </label>

                  <label className="form-field">
                    <span>Type</span>
                    <select
                      value={step.type}
                      onChange={event => updateStep(index, 'type', Number(event.target.value))}
                      required={!isDraftStep}
                    >
                      {STEP_TYPES.map(stepType => (
                        <option key={stepType.value} value={stepType.value}>
                          {stepType.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  {step.type === 1 && (
                    <label className="form-field">
                      <span>Task Definition</span>
                      <select
                        value={step.task_def_id}
                        onChange={event => updateStep(index, 'task_def_id', event.target.value)}
                        required={!isDraftStep}
                      >
                        <option value="">Select a task definition</option>
                        {taskDefs.map(taskDef => (
                          <option key={taskDef.id} value={taskDef.id}>
                            {taskDef.name} v{taskDef.version}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}

                  {step.type === 2 && (
                    <label className="form-field">
                      <span>Workflow Definition</span>
                      <select
                        value={step.workflow_def_id}
                        onChange={event => updateStep(index, 'workflow_def_id', event.target.value)}
                        required={!isDraftStep}
                      >
                        <option value="">Select a workflow definition</option>
                        {workflowDefs.map(workflowDef => (
                          <option key={workflowDef.id} value={workflowDef.id}>
                            {workflowDef.name} v{workflowDef.version}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                </div>

                <label className="form-field">
                  <span>Description</span>
                  <textarea
                    value={step.description}
                    onChange={event => updateStep(index, 'description', event.target.value)}
                    rows={5}
                    required={!isDraftStep}
                  />
                </label>

                <label className="form-field">
                  <span>Input</span>
                  <textarea
                    value={step.input}
                    onChange={event => updateStep(index, 'input', event.target.value)}
                    rows={4}
                    required={!isDraftStep}
                  />
                </label>

                <label className="checkbox-field step-return-field">
                  <input
                    type="checkbox"
                    checked={step.is_return_step}
                    onChange={event => updateStep(index, 'is_return_step', event.target.checked)}
                  />
                  <span>Return</span>
                </label>

                {isDraftStep && (
                  <div className="draft-step-actions">
                    <button type="button" className="secondary-button" onClick={addStep}>
                      Add Step
                    </button>
                  </div>
                )}

                </div>
              )
            })}
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <h3>Step Dependencies</h3>
            <button type="button" className="secondary-button" onClick={addStepDep}>
              Add Dependency
            </button>
          </div>

          {stepDeps.length === 0 ? (
            <p className="empty-note">No step dependencies defined.</p>
          ) : (
            <table className="data-table compact-edit-table">
              <thead>
                <tr>
                  <th>From</th>
                  <th>To</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {stepDeps.map((stepDep, index) => {
                  const addedSteps = steps.slice(0, -1)

                  return (
                    <tr key={index}>
                      <td>
                        <select
                          value={stepDep.source_step_def_key}
                          onChange={event => updateStepDep(index, 'source_step_def_key', event.target.value)}
                          required
                        >
                          <option value="">Select a source step</option>
                          {addedSteps.map(step => (
                            <option key={step.key} value={step.key}>
                              {step.key}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          value={stepDep.destination_step_def_key}
                          onChange={event => updateStepDep(index, 'destination_step_def_key', event.target.value)}
                          required
                        >
                          <option value="">Select a destination step</option>
                          {addedSteps.map(step => (
                            <option key={step.key} value={step.key}>
                              {step.key}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="table-actions">
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => removeStepDep(index)}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </section>

        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Workflow Definition'}
          </button>
        </div>
      </form>
    </div>
  )
}
