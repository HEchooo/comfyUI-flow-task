<template>
  <el-card class="page-card" v-loading="loading">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">系统设置</div>
          <div class="page-subtitle">配置 ComfyUI 服务器与端口池</div>
        </div>
      </div>
    </template>

    <el-form label-position="top" class="settings-form">
      <el-form-item label="ComfyUI 服务器 IP / Host">
        <el-input
          v-model="form.server_ip"
          placeholder="例如：34.59.208.230"
          clearable
          :disabled="saving"
        />
      </el-form-item>

      <el-form-item label="端口列表">
        <el-input
          v-model="form.portsText"
          type="textarea"
          :rows="3"
          :disabled="saving"
          placeholder="支持格式：8189-8198,8201"
        />
        <div class="ports-help">支持逗号分隔和区间写法，自动去重排序。</div>
      </el-form-item>
    </el-form>

    <div class="ports-preview">
      <div class="preview-title">解析结果</div>
      <div v-if="parsedPorts.length" class="ports-tags">
        <el-tag v-for="port in parsedPorts" :key="port" type="info">:{{ port }}</el-tag>
      </div>
      <el-empty v-else description="暂无可用端口" :image-size="60" />
    </div>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchComfyuiSettings, updateComfyuiSettings } from '../api/settings'
import { isDuplicateRequestError } from '../api/http'

const loading = ref(false)
const saving = ref(false)
const form = reactive({
  server_ip: '',
  portsText: ''
})

const parsedPorts = computed(() => {
  try {
    return parsePorts(form.portsText)
  } catch {
    return []
  }
})

function parsePorts(value) {
  const text = String(value || '').trim()
  if (!text) {
    return []
  }
  const result = new Set()
  const segments = text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  for (const segment of segments) {
    if (segment.includes('-')) {
      const [startRaw, endRaw] = segment.split('-', 2)
      const start = Number(startRaw)
      const end = Number(endRaw)
      if (!Number.isInteger(start) || !Number.isInteger(end)) {
        throw new Error('端口区间格式错误')
      }
      const minValue = Math.min(start, end)
      const maxValue = Math.max(start, end)
      for (let port = minValue; port <= maxValue; port += 1) {
        if (port < 1 || port > 65535) throw new Error('端口范围必须在 1-65535')
        result.add(port)
      }
      continue
    }
    const port = Number(segment)
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new Error(`无效端口: ${segment}`)
    }
    result.add(port)
  }

  return [...result].sort((a, b) => a - b)
}

function toPortsText(ports) {
  return (ports || []).join(',')
}

async function loadSettings() {
  loading.value = true
  try {
    const data = await fetchComfyuiSettings()
    form.server_ip = data.server_ip || ''
    form.portsText = toPortsText(data.ports || [])
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '加载设置失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (saving.value) return
  const serverIp = String(form.server_ip || '').trim()
  if (!serverIp) {
    ElMessage.error('请填写 ComfyUI 服务器 IP / Host')
    return
  }

  let ports = []
  try {
    ports = parsePorts(form.portsText)
  } catch (error) {
    ElMessage.error(error?.message || '端口格式错误')
    return
  }
  if (!ports.length) {
    ElMessage.error('请至少配置一个端口')
    return
  }

  saving.value = true
  try {
    const data = await updateComfyuiSettings({
      server_ip: serverIp,
      ports
    })
    form.server_ip = data.server_ip || serverIp
    form.portsText = toPortsText(data.ports || ports)
    ElMessage.success('ComfyUI 设置已保存')
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '保存设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.page-card {
  animation: rise 0.35s ease;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #153f7f;
}

.page-subtitle {
  font-size: 13px;
  color: #60748f;
  margin-top: 2px;
}

.settings-form {
  max-width: 760px;
}

.ports-help {
  font-size: 12px;
  color: #6b7d98;
  margin-top: 8px;
}

.ports-preview {
  margin-top: 14px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #dce8fb;
  background: #f7fbff;
}

.preview-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f4b87;
  margin-bottom: 10px;
}

.ports-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.actions {
  margin-top: 18px;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
