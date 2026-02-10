export const TASK_STATUS_OPTIONS = [
  { label: 'pending', value: 'pending', type: 'warning' },
  { label: 'running', value: 'running', type: 'primary' },
  { label: 'success', value: 'success', type: 'success' },
  { label: 'fail', value: 'fail', type: 'danger' }
]

export function taskStatusType(status) {
  const found = TASK_STATUS_OPTIONS.find((item) => item.value === status)
  return found?.type || 'info'
}
