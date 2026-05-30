import { formatWorkflowTime } from './Workflow'
import WorkflowState from './WorkflowState'

export default function WorkflowSummary({ workflow }) {
  if (!workflow) return null

  const workflowUrl = `#${new URLSearchParams({
    activeView: 'workflows',
    workflowId: workflow.id,
    workflowView: 'detail',
  }).toString()}`

  return (
    <tr>
      <td>
        <WorkflowState state={workflow.state} />
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
