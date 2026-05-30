export const STATE_LABEL = {
  CREATED: 'Created',
  SUBMITTED: 'Submitted',
  RUNNING: 'Running',
  SUCCEEDED: 'Succeeded',
  FAILED: 'Failed',
}

export const STATE_COLOR = {
  CREATED: '#505050',
  SUBMITTED: '#505050',
  RUNNING: '#00ff00',
  SUCCEEDED: '#007700',
  FAILED: '#ff0000',
}

export function getStateColor(state, fallback = '#64748b') {
  return STATE_COLOR[state] ?? fallback
}

export function getStateLabel(state) {
  return STATE_LABEL[state] ?? state
}

export default function WorkflowState({ state }) {
  if (state == null) return <span className="empty-note">—</span>

  return (
    <span className="state-badge" style={{ background: getStateColor(state) }}>
      {getStateLabel(state)}
    </span>
  )
}
