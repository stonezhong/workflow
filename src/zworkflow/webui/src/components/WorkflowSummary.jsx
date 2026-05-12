import { STATE_COLOR, STATE_LABEL } from './Workflow'

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
    <div className="workflow-summary">
      <span className="def-name">
        <a href={workflowUrl}>{workflow.title}</a>
      </span>
      <span className="state-badge" style={{ background: stateColor }}>
        {stateLabel}
      </span>
    </div>
  )
}
