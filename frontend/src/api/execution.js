import http from './http'

export async function uploadWorkflow(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post('/uploads/workflow', formData)
  return data
}

export async function executeTask(taskId, payload) {
  const { data } = await http.post(`/execution/task/${taskId}`, payload)
  return data
}

export async function cancelExecutionTask(taskId) {
  const { data } = await http.post(`/execution/task/${taskId}/cancel`)
  return data
}

export function createExecutionWs(taskId) {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const wsBase = apiBase.replace(/^http/, 'ws')
  return new WebSocket(`${wsBase}/execution/ws/${taskId}`)
}
