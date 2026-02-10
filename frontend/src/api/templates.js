import http from './http'

export async function fetchTaskTemplates(params) {
  const { data } = await http.get('/task-templates', { params })
  return data
}

export async function fetchTaskTemplate(templateId) {
  const { data } = await http.get(`/task-templates/${templateId}`)
  return data
}

export async function createTaskTemplate(payload) {
  const { data } = await http.post('/task-templates', payload)
  return data
}

export async function patchTaskTemplate(templateId, payload) {
  const { data } = await http.patch(`/task-templates/${templateId}`, payload)
  return data
}

export async function deleteTaskTemplate(templateId) {
  const { data } = await http.delete(`/task-templates/${templateId}`)
  return data
}

export async function createTaskFromTemplate(templateId, payload = {}) {
  const { data } = await http.post(`/task-templates/${templateId}/create-task`, payload)
  return data
}
