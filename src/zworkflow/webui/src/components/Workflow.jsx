import { useEffect, useState } from 'react'
import { listWorkflowEvents, restartFailedWorkflow } from '../../ZWorkflowClient'
import DagView from './DagView'
import PopupPanel from './PopupPanel'
import StepDefView from './StepDefView'

export const STATE_LABEL = { 
    1: 'Created', 
    2: 'run requested',
    3: 'running',
    4: "succeeded",
    5: "failed"
}
export const STATE_COLOR = { 
    1: '#505050', 
    2: '#505050', 
    3: '#00ff00',
    4: '#007700',
    5: '#ff0000'
}
const TASK_STATE_LABEL = {
  1: 'Created',
  2: 'Submitted',
  3: 'Running',
  4: 'Succeeded',
  5: 'Failed',
}
const EVENT_TYPE_LABEL = {
  WORKFLOW_SUBMITTED: 'workflow submitted',
  WORKFLOW_EXECUTION_STARTED: 'workflow started',
  WORKFLOW_EXECUTION_SUCCEEDED: 'workflow succeeded',
  WORKFLOW_EXECUTION_FAILED: 'workflow failed',
  TASK_SUBMITTED: 'task submitted',
  TASK_EXECUTION_STARTED: 'task started',
  TASK_EXECUTION_SUCCEEDED: 'task succeeded',
  TASK_EXECUTION_FAILED: 'task failed',
  TASK_OUTPUT: 'task message',
}

export function formatWorkflowTime(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  const pad = number => String(number).padStart(2, '0')

  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join('-') + ' ' + [
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join(':')
}

function getStepTimeCreated(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.time_created : undefined;
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.time_created : undefined;
    }
    return undefined;
}

function getStepTimeStarted(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.time_started : undefined;
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.time_started : undefined;
    }
    return undefined;
}

function getStepTimeEnded(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.time_ended : undefined;
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.time_ended : undefined;
    }
    return undefined;
}

function getStepInput(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.input : undefined;
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.input : undefined;
    }
    return undefined;
}

function getStepOutput(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.output : undefined;
    }
    
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.output : undefined;
    }
    return undefined;
}

function getStepState(step) {
    if (step.step_def.type === 1) {
        return step.invoke_task ? step.invoke_task.state : null;
    }
    if (step.step_def.type === 2) {
        return step.invoke_workflow ? step.invoke_workflow.state : null;
    }
    return null;
}

function JsonButton({ value, label, onShow }) {
  const hasValue = value !== undefined

  if (!hasValue) {
    return <span className="empty-note">—</span>
  }

  return (
    <div className="foldable-schema">
      <button
        type="button"
        className="schema-toggle icon-button json-view-button"
        aria-haspopup="dialog"
        aria-label={`Show ${label}`}
        title={`Show ${label}`}
        onClick={() => onShow({ value, label })}
      >
        <span className="magnifier-icon" aria-hidden="true" />
      </button>
    </div>
  )
}

export default function Workflow({ workflow, onWorkflowUpdated }) {
  const [restartError, setRestartError] = useState(null)
  const [isRestarting, setIsRestarting] = useState(false)
  const [selectedJson, setSelectedJson] = useState(null)
  const [selectedStepDef, setSelectedStepDef] = useState(null)
  const [events, setEvents] = useState([])
  const [eventsError, setEventsError] = useState(null)

  useEffect(() => {
    if (!workflow?.id) return undefined

    let isMounted = true

    const reloadEvents = () => {
      listWorkflowEvents(workflow.id)
        .then(nextEvents => {
          if (!isMounted) return
          setEvents(nextEvents)
          setEventsError(null)
        })
        .catch(err => {
          if (isMounted) setEventsError(err.message)
        })
    }

    reloadEvents()
    const intervalId = window.setInterval(reloadEvents, 1000)

    return () => {
      isMounted = false
      window.clearInterval(intervalId)
    }
  }, [workflow?.id])

  if (!workflow) return null

  const stateLabel = STATE_LABEL[workflow.state] ?? workflow.state
  const stateColor = STATE_COLOR[workflow.state] ?? '#64748b'
  const canRestart = workflow.state === 5
  const steps = workflow.steps ?? []
  const stepsById = Object.fromEntries(steps.map(step => [step.id, step]))
  const stepDeps = workflow.workflow_def?.step_deps ?? []
  const workflowDefUrl = workflow.workflow_def
    ? '#' + new URLSearchParams({
      activeView: 'workflow-definitions',
      workflowDefId: workflow.workflow_def.id,
      workflowDefView: 'detail',
    }).toString()
    : null
  const dagNodes = steps.map(step => {
    const state = getStepState(step)

    return {
      key: step.step_def.key,
      title: step.step_def.title,
      color: STATE_COLOR[state] ?? '#f8fafc',
    }
  })

  const handleRestart = () => {
    setRestartError(null)
    setIsRestarting(true)

    restartFailedWorkflow(workflow.id)
      .then(updatedWorkflow => {
        onWorkflowUpdated?.(updatedWorkflow)
      })
      .catch(err => setRestartError(err.message))
      .finally(() => setIsRestarting(false))
  }

  const showStepDef = (event, stepDef) => {
    event.preventDefault()
    setSelectedStepDef(stepDef)
  }

  return (
    <div className="workflow">
      <div className="def-summary">
        <span className="state-badge" style={{ background: stateColor }}>
          {stateLabel}
        </span>
        <span className="def-name">
          {workflow.title}
        </span>
        {canRestart && (
          <button
            type="button"
            className="secondary-button workflow-restart-button"
            onClick={handleRestart}
            disabled={isRestarting}
          >
            {isRestarting ? 'Restarting...' : 'Restart'}
          </button>
        )}
      </div>
      {restartError && <div className="form-error workflow-action-error">{restartError}</div>}

      <table className="detail-table def-details">
        <tbody>
          <tr>
            <td className="detail-label">ID</td>
            <td>{workflow.id}</td>
          </tr>
          <tr>
            <td className="detail-label">Title</td>
            <td>{workflow.title}</td>
          </tr>
          <tr>
            <td className="detail-label">Description</td>
            <td>{workflow.description}</td>
          </tr>
          <tr>
            <td className="detail-label">Created</td>
            <td>{formatWorkflowTime(workflow.time_created)}</td>
          </tr>
          <tr>
            <td className="detail-label">Started</td>
            <td>{formatWorkflowTime(workflow.time_started)}</td>
          </tr>
          <tr>
            <td className="detail-label">Ended</td>
            <td>{formatWorkflowTime(workflow.time_ended)}</td>
          </tr>
          <tr>
            <td className="detail-label">State</td>
            <td>
              <span className="state-badge" style={{ background: stateColor }}>
                {stateLabel}
              </span>
            </td>
          </tr>
          <tr>
            <td className="detail-label">Workflow Def</td>
            <td>
              {workflow.workflow_def && (
                <a href={workflowDefUrl} className="step-def-link">
                  {workflow.workflow_def.name} v{workflow.workflow_def.version}
                </a>
              )}
            </td>
          </tr>
          {workflow.input && (
            <tr>
              <td className="detail-label">Input</td>
              <td><JsonButton value={workflow.input} label="input" onShow={setSelectedJson} /></td>
            </tr>
          )}
          {workflow.output && (
            <tr>
              <td className="detail-label">Output</td>
              <td><JsonButton value={workflow.output} label="output" onShow={setSelectedJson} /></td>
            </tr>
          )}
        </tbody>
      </table>

      <h3 className="section-subheading">Steps</h3>
      {steps.length === 0 ? (
        <p className="empty-note">No steps defined.</p>
      ) : (
        <table className="data-table workflow-steps-table">
          <thead>
              <tr>
                <th>State</th>
                <th>Key</th>
                <th>Title</th>
                <th>Time Created</th>
                <th>Time Started</th>
                <th>Time Ended</th>
              <th>Input</th>
              <th>Output</th>
            </tr>
          </thead>
          <tbody>
            {steps.map(step => {
              const stepDef = step.step_def;
              const stepState = getStepState(step);

              return (
              <tr key={step.id}>
                <td>{TASK_STATE_LABEL[stepState] ?? stepState ?? <span className="empty-note">—</span>}</td>
                <td>
                  <a
                    href={`#step-def-${stepDef.id}`}
                    className="step-def-link"
                    onClick={event => showStepDef(event, stepDef)}
                  >
                    <code>{stepDef.key}</code>
                  </a>
                </td>
                <td>{stepDef.title}</td>
                <td>{formatWorkflowTime(getStepTimeCreated(step))}</td>
                <td>{formatWorkflowTime(getStepTimeStarted(step))}</td>
                <td>{formatWorkflowTime(getStepTimeEnded(step))}</td>
                <td><JsonButton value={getStepInput(step)} label="input" onShow={setSelectedJson} /></td>
                <td><JsonButton value={getStepOutput(step)} label="output" onShow={setSelectedJson} /></td>
              </tr>
              )
            })}
          </tbody>
        </table>
      )}

      <h3 className="section-subheading">Step Dependencies</h3>
      <div>
        <DagView
          nodes={dagNodes}
          connections={stepDeps.map(dep => ({source: dep.source_step_def_key, destination: dep.destination_step_def_key}))}
        />
      </div>

      <h3 className="section-subheading">Events</h3>
      {eventsError && <div className="form-error workflow-action-error">{eventsError}</div>}
      {events.length === 0 ? (
        <p className="empty-note">No events recorded.</p>
      ) : (
        <table className="data-table workflow-events-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>Step Key</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {events.map(event => (
              <tr key={event.id}>
                <td>{formatWorkflowTime(event.event_time)}</td>
                <td>{EVENT_TYPE_LABEL[event.type] ?? event.type}</td>
                <td>{stepsById[event.step_id]?.step_def?.key ?? <span className="empty-note">—</span>}</td>
                <td>{event.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selectedJson && (
        <PopupPanel
          title={selectedJson.label}
          className="json-popup"
          onClose={() => setSelectedJson(null)}
        >
          <pre className="json-block schema-block">{JSON.stringify(selectedJson.value, null, 2)}</pre>
        </PopupPanel>
      )}

      {selectedStepDef && (
        <PopupPanel
          title="Step Definition"
          ariaLabel={`Step definition ${selectedStepDef.key}`}
          className="step-def-popup"
          onClose={() => setSelectedStepDef(null)}
        >
          <StepDefView stepDef={selectedStepDef} />
        </PopupPanel>
      )}

    </div>
  )
}
