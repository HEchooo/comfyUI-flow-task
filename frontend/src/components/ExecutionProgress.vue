<template>
  <div v-if="inline" class="inline-panel">
    <div class="progress-body">
      <div class="status-row">
        <el-tag :type="statusTagType" size="large">{{ statusLabel }}</el-tag>
        <span class="task-id-text">任务: {{ taskId }}</span>
      </div>

      <div v-if="currentProgress.max > 0" class="progress-section">
        <div class="progress-label">
          节点 {{ currentProgressNodeLabel }} — {{ currentProgress.value }} / {{ currentProgress.max }}
        </div>
        <el-progress
          :percentage="progressPercent"
          :status="execStatus === 'error' ? 'exception' : undefined"
          :striped="execStatus === 'running'"
          :striped-flow="execStatus === 'running'"
          :duration="4"
        />
      </div>

      <div v-if="currentNodeId && execStatus === 'running'" class="node-row">
        <el-icon class="spin-icon"><Loading /></el-icon>
        <span>正在执行节点 <strong>{{ currentNodeLabel }}</strong></span>
      </div>

      <div class="event-log" ref="logEl">
        <div
          v-for="(entry, idx) in eventLog"
          :key="idx"
          class="log-entry"
          :class="entry.type"
        >
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
        <div v-if="!eventLog.length" class="log-empty">等待执行事件…</div>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />

      <div v-if="execStatus === 'completed'" class="complete-banner">
        <el-icon><CircleCheckFilled /></el-icon>
        全部执行完成
      </div>
    </div>
  </div>

  <el-drawer
    v-else
    v-model="visible"
    title="执行进度"
    direction="rtl"
    size="420px"
    :before-close="handleClose"
  >
    <div class="progress-body">
      <div class="status-row">
        <el-tag :type="statusTagType" size="large">{{ statusLabel }}</el-tag>
        <span class="task-id-text">任务: {{ taskId }}</span>
      </div>

      <div v-if="currentProgress.max > 0" class="progress-section">
        <div class="progress-label">
          节点 {{ currentProgressNodeLabel }} — {{ currentProgress.value }} / {{ currentProgress.max }}
        </div>
        <el-progress
          :percentage="progressPercent"
          :status="execStatus === 'error' ? 'exception' : undefined"
          :striped="execStatus === 'running'"
          :striped-flow="execStatus === 'running'"
          :duration="4"
        />
      </div>

      <div v-if="currentNodeId && execStatus === 'running'" class="node-row">
        <el-icon class="spin-icon"><Loading /></el-icon>
        <span>正在执行节点 <strong>{{ currentNodeLabel }}</strong></span>
      </div>

      <div class="event-log" ref="logEl">
        <div
          v-for="(entry, idx) in eventLog"
          :key="idx"
          class="log-entry"
          :class="entry.type"
        >
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
        <div v-if="!eventLog.length" class="log-empty">等待执行事件…</div>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />

      <div v-if="execStatus === 'completed'" class="complete-banner">
        <el-icon><CircleCheckFilled /></el-icon>
        全部执行完成
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { CircleCheckFilled, Loading } from '@element-plus/icons-vue'

import { createExecutionWs } from '../api/execution'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  taskId: { type: String, default: '' },
  inline: { type: Boolean, default: false },
  active: { type: Boolean, default: false },
  taskStatus: { type: String, default: '' },
  initialState: { type: [Object, String], default: null }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isOpen = computed(() => (props.inline ? props.active : props.modelValue))

const execStatus = ref('idle') // idle | running | completed | error | cancelled
const currentNodeId = ref('')
const currentNodeTitle = ref('')
const currentNodeClassType = ref('')
const currentProgress = ref({ nodeId: '', nodeTitle: '', nodeClassType: '', value: 0, max: 0 })
const errorMessage = ref('')
const eventLog = ref([])
const logEl = ref(null)
const activeTaskId = ref('')
const currentPromptId = ref('')

let ws = null
let pingTimer = null
let manualDisconnect = false

const statusTagType = computed(() => {
  if (execStatus.value === 'completed') return 'success'
  if (execStatus.value === 'error') return 'danger'
  if (execStatus.value === 'cancelled') return 'warning'
  if (execStatus.value === 'running') return 'primary'
  return 'info'
})

const statusLabel = computed(() => {
  const labels = { idle: '等待中', running: '执行中', completed: '已完成', error: '执行错误', cancelled: '已取消' }
  return labels[execStatus.value] || execStatus.value
})

const progressPercent = computed(() => {
  if (!currentProgress.value.max) return 0
  return Math.round((currentProgress.value.value / currentProgress.value.max) * 100)
})

const currentNodeLabel = computed(() =>
  formatNodeLabel(currentNodeId.value, currentNodeTitle.value, currentNodeClassType.value)
)

const currentProgressNodeLabel = computed(() =>
  formatNodeLabel(
    currentProgress.value.nodeId,
    currentProgress.value.nodeTitle,
    currentProgress.value.nodeClassType
  )
)

function nowTime() {
  return new Date().toLocaleTimeString()
}

function formatNodeLabel(nodeId, nodeTitle, nodeClassType) {
  if (!nodeId) return '-'
  if (nodeTitle) return `${nodeId} (${nodeTitle})`
  if (nodeClassType) return `${nodeId} (${nodeClassType})`
  return String(nodeId)
}

function addLog(message, type = 'info') {
  const last = eventLog.value[eventLog.value.length - 1]
  if (last && last.message === message && last.type === type) {
    return
  }
  eventLog.value.push({ time: nowTime(), message, type })
  nextTick(() => {
    if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
  })
}

function resetState() {
  execStatus.value = 'idle'
  currentNodeId.value = ''
  currentNodeTitle.value = ''
  currentNodeClassType.value = ''
  currentProgress.value = { nodeId: '', nodeTitle: '', nodeClassType: '', value: 0, max: 0 }
  errorMessage.value = ''
  eventLog.value = []
  currentPromptId.value = ''
}

function parseExecutionStateInput(raw) {
  if (!raw) return null
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : null
    } catch {
      return null
    }
  }
  if (typeof raw === 'object') {
    return raw
  }
  return null
}

function applyStateSync(data, options = {}) {
  const { appendSyncLog = true } = options
  const status = data.status
  if (status === 'running') execStatus.value = 'running'
  else if (status === 'success') execStatus.value = 'completed'
  else if (status === 'fail') execStatus.value = 'error'
  else if (status === 'cancelled') execStatus.value = 'cancelled'

  const progress = data.progress || {}
  currentProgress.value = {
    nodeId: progress.node_id || '',
    nodeTitle: progress.node_title || '',
    nodeClassType: progress.node_class_type || '',
    value: Number(progress.value || 0),
    max: Number(progress.max || 0)
  }
  currentNodeId.value = data.current_node_id || ''
  currentNodeTitle.value = data.current_node_title || ''
  currentNodeClassType.value = data.current_node_class_type || ''
  if (data.prompt_id) {
    currentPromptId.value = data.prompt_id
  }
  if (data.error_message) {
    errorMessage.value = data.error_message
  }
  if (Array.isArray(data.event_log)) {
    eventLog.value = data.event_log.map((entry) => ({
      time: entry?.time || nowTime(),
      message: String(entry?.message || ''),
      type: entry?.type || 'info'
    }))
    nextTick(() => {
      if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
    })
  }
  if (appendSyncLog) {
    addLog(`已同步服务端状态: ${status || 'unknown'}`, 'info')
  }
}

function hydrateFromInitialState() {
  const parsed = parseExecutionStateInput(props.initialState)
  if (!parsed) return
  applyStateSync(parsed, { appendSyncLog: false })
}

function connectWs() {
  disconnectWs()
  if (!props.taskId) return

  manualDisconnect = false
  ws = createExecutionWs(props.taskId)

  ws.onopen = () => {
    if (execStatus.value === 'idle') {
      execStatus.value = 'running'
    }
    addLog('WebSocket 已连接，等待 ComfyUI 事件…', 'info')
  }

  ws.onmessage = (event) => {
    let message
    try {
      message = JSON.parse(event.data)
    } catch {
      return
    }
    handleMessage(message)
  }

  ws.onerror = () => {
    if (manualDisconnect) return
    if (execStatus.value === 'running') {
      addLog('WebSocket 连接错误', 'error')
      execStatus.value = 'error'
    }
  }

  ws.onclose = () => {
    if (manualDisconnect) return
    if (execStatus.value === 'running') {
      addLog('WebSocket 连接已断开', 'error')
      execStatus.value = 'error'
    }
  }

  pingTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    } else {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }, 20000)
}

function handleMessage(message) {
  const type = message.type
  const data = message.data || {}

  if (type === 'state_sync') {
    applyStateSync(data)
    if (data.status && data.status !== 'running') {
      disconnectWs()
    }
    return
  }

  if (type === 'execution_start') {
    const promptId = message.prompt_id || data.prompt_id || ''
    if (promptId && currentPromptId.value && promptId !== currentPromptId.value) {
      // Same task executed again: replace old run logs instead of append.
      resetState()
    }
    if (promptId) {
      currentPromptId.value = promptId
    }
    execStatus.value = 'running'
    errorMessage.value = ''
    addLog('执行开始', 'info')
    return
  }

  if (type === 'executing') {
    const nodeId = data.node_id
    if (nodeId) {
      currentNodeId.value = nodeId
      currentNodeTitle.value = data.node_title || ''
      currentNodeClassType.value = data.node_class_type || ''
      addLog(`执行节点: ${formatNodeLabel(nodeId, data.node_title, data.node_class_type)}`, 'info')
    }
    return
  }

  if (type === 'progress') {
    currentProgress.value = {
      nodeId: data.node_id || '',
      nodeTitle: data.node_title || '',
      nodeClassType: data.node_class_type || '',
      value: data.value || 0,
      max: data.max || 0
    }
    return
  }

  if (type === 'executed') {
    addLog(`节点 ${formatNodeLabel(data.node_id, data.node_title, data.node_class_type)} 执行完毕`, 'success')
    return
  }

  if (type === 'execution_cached') {
    const nodeInfos = Array.isArray(data.node_infos) ? data.node_infos : []
    if (nodeInfos.length) {
      const labels = nodeInfos.map((item) =>
        formatNodeLabel(item.node_id, item.node_title, item.node_class_type)
      )
      addLog(`缓存节点: ${labels.join(', ')}`, 'info')
      return
    }
    const nodes = Array.isArray(data.nodes) ? data.nodes : []
    if (nodes.length) addLog(`缓存节点: ${nodes.join(', ')}`, 'info')
    return
  }

  if (type === 'execution_error') {
    const errMsg = data.exception_message || '未知错误'
    const nodeLabel = formatNodeLabel(data.node_id, data.node_title, data.node_class_type)
    errorMessage.value = `节点 ${nodeLabel} 错误: ${errMsg}`
    addLog(errorMessage.value, 'error')
    execStatus.value = 'error'
    return
  }

  if (type === 'all_completed') {
    const finalStatus = data.status
    currentNodeId.value = ''
    currentNodeTitle.value = ''
    currentNodeClassType.value = ''
    if (finalStatus === 'fail') {
      execStatus.value = 'error'
      addLog('执行结束，存在错误', 'error')
    } else if (finalStatus === 'cancelled') {
      execStatus.value = 'cancelled'
      addLog('执行已取消', 'warning')
    } else {
      execStatus.value = 'completed'
      addLog('所有节点执行完成 ✓', 'success')
    }
    disconnectWs()
    return
  }

  if (type === 'listener_error') {
    errorMessage.value = data.message || 'ComfyUI 连接失败'
    addLog(errorMessage.value, 'error')
    execStatus.value = 'error'
  }
}

function disconnectWs() {
  manualDisconnect = true
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}

function handleClose() {
  disconnectWs()
  visible.value = false
}

watch(
  () => [props.taskId, props.initialState],
  ([taskId]) => {
    if (!taskId) return
    if (taskId !== activeTaskId.value) {
      resetState()
      activeTaskId.value = taskId
    }
    if (props.taskStatus !== 'running') {
      hydrateFromInitialState()
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => [isOpen.value, props.taskId, props.taskStatus],
  ([open, taskId, taskStatus]) => {
    if (open && taskId) {
      if (taskId !== activeTaskId.value) {
        resetState()
        activeTaskId.value = taskId
      }
      if (taskStatus !== 'running') {
        disconnectWs()
        hydrateFromInitialState()
      } else if (!ws) {
        connectWs()
      }
      return
    }
    if (!open) {
      disconnectWs()
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  disconnectWs()
})
</script>

<style scoped>
.inline-panel {
  padding: 12px;
  border: 1px solid #dce8fb;
  border-radius: 10px;
  background: linear-gradient(180deg, #fafcff 0%, #f5f9ff 100%);
}

.progress-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 0;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.task-id-text {
  font-size: 12px;
  color: #7a96bb;
  word-break: break-all;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-label {
  font-size: 12px;
  color: #4a6283;
}

.node-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #2a4a80;
}

.spin-icon {
  animation: spin 1.2s linear infinite;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.event-log {
  border: 1px solid #dce8fb;
  border-radius: 8px;
  background: #f7faff;
  padding: 10px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.event-log::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}

.log-entry {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.log-time {
  color: #9aaecc;
  flex-shrink: 0;
}

.log-msg {
  color: #2a3f62;
}

.log-entry.success .log-msg {
  color: #67c23a;
}

.log-entry.error .log-msg {
  color: #f56c6c;
}

.log-entry.warning .log-msg {
  color: #e6a23c;
}

.log-empty {
  font-size: 12px;
  color: #aabbcc;
  text-align: center;
  padding: 20px 0;
}

.error-alert {
  margin-top: 4px;
}

.complete-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #67c23a;
  padding: 10px 0;
}
</style>
