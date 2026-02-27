<template>
  <el-dialog
    v-model="visible"
    width="min(960px, 94vw)"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    :show-close="!submitting"
    title="选择执行端口"
    @closed="handleClosed"
  >
    <div class="dialog-content" v-loading="submitting" element-loading-text="任务提交中，请稍候...">
      <div class="dialog-toolbar">
        <div class="toolbar-left">
          <el-tag v-if="taskTitle" type="success">任务: {{ taskTitle }}</el-tag>
          <el-tag type="info">服务器: {{ serverIp || '-' }}</el-tag>
          <span class="refresh-time">刷新时间: {{ refreshedAtText }}</span>
        </div>
        <el-button :loading="loading" :disabled="submitting" @click="refreshStatus">立即刷新</el-button>
      </div>

      <div v-if="showSkeleton" class="port-grid">
        <div v-for="idx in skeletonCount" :key="`skeleton-${idx}`" class="port-card skeleton-card">
          <div class="skeleton-line skeleton-title" />
          <div class="skeleton-line skeleton-tag" />
          <div class="skeleton-line skeleton-row" />
          <div class="skeleton-line skeleton-row" />
          <div class="skeleton-line skeleton-url" />
        </div>
      </div>
      <div v-else-if="items.length" class="port-grid">
        <button
          v-for="item in items"
          :key="item.port"
          class="port-card"
          :class="[levelClass(item.level), { selected: selectedPort === item.port, disabled: !item.reachable || submitting }]"
          :disabled="!item.reachable || submitting"
          @click="selectedPort = item.port"
        >
          <div class="card-top">
            <div class="port-title">:{{ item.port }}</div>
            <el-tag size="small" :type="levelTagType(item.level)">{{ levelLabel(item.level) }}</el-tag>
          </div>
          <div class="card-line">运行中: {{ item.running_count }}</div>
          <div class="card-line">排队中: {{ item.pending_count }}</div>
          <div class="card-url">{{ item.base_url }}</div>
          <div v-if="item.error" class="card-error">{{ item.error }}</div>
        </button>
      </div>
      <el-empty v-else description="暂无端口配置，请先到设置页配置" :image-size="72" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button :disabled="submitting" @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!selectedEndpoint || submitting" @click="handleConfirm">
          {{ submitting ? '任务提交中...' : '确认执行' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchComfyuiPortStatus } from '../api/settings'
import { isDuplicateRequestError } from '../api/http'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  taskTitle: { type: String, default: '' },
  submitting: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const serverIp = ref('')
const refreshedAtText = ref('-')
const items = ref([])
const selectedPort = ref(null)
const skeletonCount = 6
let refreshTimer = null

const showSkeleton = computed(() => loading.value && !items.value.length)

const selectedEndpoint = computed(() => {
  const port = selectedPort.value
  if (!port) return null
  const item = items.value.find((entry) => entry.port === port && entry.reachable)
  if (!item) return null
  return {
    server_ip: serverIp.value,
    port: item.port,
    base_url: item.base_url
  }
})

function levelLabel(level) {
  const map = {
    idle: '空闲',
    running: '运行中',
    queued: '排队中',
    overloaded: '排队拥塞',
    unreachable: '不可达'
  }
  return map[level] || level
}

function levelTagType(level) {
  if (level === 'idle') return 'primary'
  if (level === 'running') return 'warning'
  if (level === 'queued') return 'warning'
  if (level === 'overloaded') return 'danger'
  return 'info'
}

function levelClass(level) {
  if (level === 'idle') return 'level-idle'
  if (level === 'running') return 'level-running'
  if (level === 'queued') return 'level-queued'
  if (level === 'overloaded') return 'level-overloaded'
  return 'level-unreachable'
}

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleTimeString()
}

async function refreshStatus() {
  loading.value = true
  try {
    const data = await fetchComfyuiPortStatus()
    serverIp.value = data.server_ip || ''
    refreshedAtText.value = formatTime(data.refreshed_at)
    items.value = Array.isArray(data.items) ? data.items : []
    if (!items.value.find((item) => item.port === selectedPort.value && item.reachable)) {
      selectedPort.value = null
    }
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '获取端口状态失败')
  } finally {
    loading.value = false
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    refreshStatus()
  }, 5000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function handleConfirm() {
  if (!selectedEndpoint.value) return
  emit('confirm', selectedEndpoint.value)
}

function handleClosed() {
  stopAutoRefresh()
  items.value = []
  selectedPort.value = null
}

watch(
  () => visible.value,
  async (open) => {
    if (!open) {
      stopAutoRefresh()
      return
    }
    await refreshStatus()
    startAutoRefresh()
  }
)

onBeforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.refresh-time {
  font-size: 12px;
  color: #6f84a7;
}

.port-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.dialog-content {
  min-height: 220px;
}

.port-card {
  text-align: left;
  padding: 12px;
  border: 1px solid #d8e5f8;
  border-radius: 10px;
  background: #f9fbff;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}

.port-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(23, 63, 127, 0.12);
}

.port-card.disabled {
  cursor: not-allowed;
  opacity: 0.78;
}

.port-card.selected {
  border-width: 2px;
  box-shadow: 0 8px 22px rgba(23, 63, 127, 0.18);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.port-title {
  font-size: 17px;
  font-weight: 700;
  color: #143f7f;
}

.card-line {
  font-size: 12px;
  color: #2c4971;
  margin-top: 4px;
}

.card-url {
  margin-top: 8px;
  font-size: 11px;
  color: #6886b0;
  word-break: break-all;
}

.card-error {
  margin-top: 6px;
  font-size: 11px;
  color: #d63636;
  line-height: 1.4;
}

.skeleton-card {
  position: relative;
  overflow: hidden;
  cursor: default;
  background: #f6f9ff;
  border-color: #e2ebf8;
}

.skeleton-card::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.68), transparent);
  animation: skeleton-shimmer 1.35s ease-in-out infinite;
}

.skeleton-line {
  background: #e5eefb;
  border-radius: 6px;
}

.skeleton-title {
  width: 44%;
  height: 22px;
  margin-bottom: 8px;
}

.skeleton-tag {
  width: 35%;
  height: 20px;
  margin-bottom: 12px;
}

.skeleton-row {
  width: 62%;
  height: 12px;
  margin-bottom: 8px;
}

.skeleton-url {
  width: 90%;
  height: 11px;
  margin-top: 8px;
}

@keyframes skeleton-shimmer {
  100% {
    transform: translateX(100%);
  }
}

.level-idle {
  border-color: #7db9ff;
  background: linear-gradient(180deg, #f3f9ff 0%, #eaf4ff 100%);
}

.level-running {
  border-color: #ffb36a;
  background: linear-gradient(180deg, #fff8ef 0%, #fff1dd 100%);
}

.level-queued {
  border-color: #ffd87a;
  background: linear-gradient(180deg, #fffced 0%, #fff7d8 100%);
}

.level-overloaded {
  border-color: #ff8f8f;
  background: linear-gradient(180deg, #fff3f3 0%, #ffe2e2 100%);
}

.level-unreachable {
  border-color: #d8dee8;
  background: linear-gradient(180deg, #f8f9fb 0%, #f2f4f8 100%);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
