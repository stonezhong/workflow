import { STATE_COLOR, STATE_LABEL, formatWorkflowTime } from './Workflow'

export default function WorkflowSummary({ workflow }) {
  if (!workflow) return null

  const stateLabel = STATE_LABEL[workflow.state] ?? workflow.state
  const stateColor = STATE_COLOR[workflow.state] ?? '#64748b'
  const workflowUrl = `#${new URLSearchParams({
    activeView: 'workflows',
    workflowId: workflow.id,
    workflowView: 'detail',
  }).toString()}`

  return (
    <tr>
      <td>
        <span className="state-badge" style={{ background: stateColor }}>
          {stateLabel}
        </span>
      </td>
      <td>
        <a href={workflowUrl}>{workflow.title}</a>
      </td>
      <td>{formatWorkflowTime(workflow.time_created)}</td>
      <td>{formatWorkflowTime(workflow.time_started)}</td>
      <td>{formatWorkflowTime(workflow.time_ended)}</td>
    </tr>
  )
}
