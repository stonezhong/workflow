const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

// ── Workflow Definitions ──────────────────────────────────────

export function listWorkflowDefs() {
  return request('/workflow_defs')
}

export function getWorkflowDef(workflowDefId) {
  return request(`/workflow_defs/${workflowDefId}`)
}

export function createWorkflowDef(details) {
  return request('/workflow_defs', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

// ── Task Definitions ──────────────────────────────────────────

export function listTaskDefs() {
  return request('/task_defs')
}

export function getTaskDef(taskDefId) {
  return request(`/task_defs/${taskDefId}`)
}

export function createTaskDef(details) {
  return request('/task_defs', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

// ── Schemas ────────────────────────────────────────────────

export function listSchemas() {
  return request('/schemas')
}

// ── Workflows ─────────────────────────────────────────────────

export function listWorkflows() {
  return request('/workflows')
}

export function getWorkflow(workflowId) {
  return request(`/workflows/${workflowId}`)
}

export function createWorkflow(details) {
  return request('/workflows', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

export function restartFailedWorkflow(workflowId) {
  return request(`/workflows/${workflowId}/restart`, {
    method: 'POST',
  })
}
