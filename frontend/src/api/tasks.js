import http from './http'

export async function fetchTasks(params) {
  const { data } = await http.get('/tasks', { params })
  return data
}

export async function fetchTask(taskId) {
  const { data } = await http.get(`/tasks/${taskId}`)
  return data
}

export async function createTask(payload) {
  const { data } = await http.post('/tasks', payload)
  return data
}

export async function patchTask(taskId, payload) {
  const { data } = await http.patch(`/tasks/${taskId}`, payload)
  return data
}

export async function deleteTask(taskId) {
  const { data } = await http.delete(`/tasks/${taskId}`)
  return data
}

export async function patchSubtask(subtaskId, payload) {
  const { data } = await http.patch(`/subtasks/${subtaskId}`, payload)
  return data
}

export async function patchTaskStatus(taskId, payload) {
  const { data } = await http.patch(`/tasks/${taskId}/status`, payload)
  return data
}

export async function patchSubtaskStatus(subtaskId, payload) {
  const { data } = await http.patch(`/subtasks/${subtaskId}/status`, payload)
  return data
}

export async function uploadImageByFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post('/uploads/image', formData)
  return data
}
