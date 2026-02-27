<template>
  <el-card v-loading="loading" class="page-card">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">任务详情</div>
          <div class="page-subtitle">查看任务与子任务执行配置</div>
        </div>
        <div class="actions">
          <el-button @click="$router.push('/')">返回列表</el-button>
          <el-button type="danger" plain :loading="deleting" :disabled="!task.id || deleting" @click="handleDelete">删除</el-button>
          <el-button type="primary" @click="$router.push(`/tasks/${task.id}/edit`)" :disabled="!task.id">编辑</el-button>
          <el-tooltip v-if="canExecute" :content="!task.workflow_json ? '请先上传工作流' : '执行 ComfyUI 工作流'" placement="top">
            <span>
              <el-button
                type="success"
                :disabled="!task.id || !task.workflow_json || executing || cancelling"
                :loading="executing"
                @click="handleExecute"
              >
                执行
              </el-button>
            </span>
          </el-tooltip>
          <el-button
            v-if="task.status === 'running'"
            type="warning"
            plain
            :disabled="!task.id || cancelling || executing"
            :loading="cancelling"
            @click="handleCancel"
          >
            取消执行
          </el-button>
        </div>
      </div>
    </template>

    <template v-if="task.id">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ task.title }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="taskStatusType(task.status)">{{ task.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(task.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(task.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ task.description || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- Workflow info -->
      <div v-if="task.workflow_json" class="workflow-banner">
        <el-icon class="workflow-icon"><Document /></el-icon>
        <span class="workflow-label">ComfyUI 工作流已配置</span>
        <el-tag size="small" type="info">{{ task.workflow_filename || 'workflow.json' }}</el-tag>
        <el-tag size="small" type="success">{{ Object.keys(task.workflow_json).length }} 个节点</el-tag>
        <el-button text type="primary" size="small" @click="workflowJsonDialog = true">查看 JSON</el-button>
      </div>
      <div v-else class="workflow-banner workflow-banner--empty">
        <el-icon><Warning /></el-icon>
        <span>未配置 ComfyUI 工作流，前往编辑页面上传</span>
      </div>

      <div v-if="showProgressPanel" class="detail-progress">
        <ExecutionProgress
          inline
          :task-id="String(task.id)"
          :task-status="String(task.status || '')"
          :initial-state="parsedExecutionState"
          :active="true"
        />
      </div>

      <h3 class="section-title">子任务列表</h3>
      <div v-if="!task.subtasks?.length">
        <el-empty description="无子任务" />
      </div>

      <el-card v-for="item in task.subtasks" :key="item.id" class="subtask-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="子任务ID">{{ item.id }}</el-descriptions-item>
          <el-descriptions-item label="平台">{{ item.platform }}</el-descriptions-item>
          <el-descriptions-item label="账号名称">{{ item.account_name }}</el-descriptions-item>
          <el-descriptions-item label="账号编号">{{ item.account_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="taskStatusType(item.status)">{{ item.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ formatDate(item.publish_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="result-panel" v-if="hasResult(item)">
          <div class="result-header">
            <div class="result-title">子任务结果</div>
            <el-button text type="primary" @click="openResultJson(item)">查看原始 JSON</el-button>
          </div>

          <div v-if="hasRawOutput(item)" class="raw-output-card">
            <div class="raw-output-title">结果摘要</div>
            <div class="raw-output-preview">{{ getRawOutputPreview(item) }}</div>
            <el-button text type="primary" @click="openResultMarkdown(item.result.raw_output)">查看全文</el-button>
          </div>

          <div v-if="getStructuredResultEntries(item).length" class="result-kv-grid">
            <div class="result-kv-item" v-for="[key, value] in getStructuredResultEntries(item)" :key="`${item.id}-${key}`">
              <div class="result-kv-key">{{ key }}</div>
              <pre class="result-kv-value">{{ formatResultValue(value) }}</pre>
            </div>
          </div>
        </div>

        <div v-if="hasPrompt(item)" class="prompt-list">
          <div class="prompt-item" v-for="(prompt, idx) in getPrompts(item)" :key="`${item.id}-prompt-${idx}`">
            <div class="prompt-label">提示词 {{ idx + 1 }}</div>
            <div class="prompt-snippet">{{ prompt }}</div>
            <el-button text type="primary" @click="openPromptPreview(prompt, `子任务提示词 ${idx + 1}`)">Markdown 预览</el-button>
          </div>
        </div>

        <div class="photo-grid">
          <div class="photo-card" v-for="(photo, photoIndex) in item.photos" :key="photo.id">
            <el-image
              class="preview-image"
              :src="photo.url"
              fit="contain"
              :preview-src-list="getPhotoUrls(item)"
              :initial-index="photoIndex"
              preview-teleported
              hide-on-click-modal
            />
          </div>
        </div>

        <div class="generated-section">
          <div class="generated-title">生图结果</div>
          <div class="photo-grid" v-if="getGeneratedImages(item).length">
            <div class="photo-card generated-photo-card" v-for="(image, imageIndex) in getGeneratedImages(item)" :key="image.id">
              <el-image
                class="preview-image"
                :src="image.url"
                fit="contain"
                :preview-src-list="getGeneratedImageUrls(item)"
                :initial-index="imageIndex"
                preview-teleported
                hide-on-click-modal
              />
              <div class="sort-chip">#{{ image.sort_order }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无生图结果" :image-size="60" />
        </div>
      </el-card>
    </template>

    <el-dialog v-model="previewDialog.visible" :title="previewDialog.title" width="min(780px, 92vw)" append-to-body>
      <div class="markdown-body preview-dialog-body" v-if="previewDialog.html" v-html="previewDialog.html"></div>
      <el-empty v-else description="暂无内容" />
    </el-dialog>

    <el-dialog v-model="resultJsonDialog.visible" :title="resultJsonDialog.title" width="min(820px, 94vw)" append-to-body>
      <pre class="result-json-dialog">{{ resultJsonDialog.content }}</pre>
    </el-dialog>

    <el-dialog v-model="workflowJsonDialog" title="工作流 JSON" width="min(820px, 94vw)" append-to-body>
      <pre class="result-json-dialog">{{ workflowJsonPreview }}</pre>
    </el-dialog>
  </el-card>

</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Warning } from '@element-plus/icons-vue'

import ExecutionProgress from '../components/ExecutionProgress.vue'
import { deleteTask, fetchTask } from '../api/tasks'
import { cancelExecutionTask, executeTask } from '../api/execution'
import { isDuplicateRequestError } from '../api/http'
import { renderMarkdown } from '../utils/markdown'
import { taskStatusType } from '../utils/status'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const deleting = ref(false)
const executing = ref(false)
const cancelling = ref(false)
const task = reactive({})
const workflowJsonDialog = ref(false)

const previewDialog = reactive({
  visible: false,
  title: 'Markdown 预览',
  html: ''
})
const resultJsonDialog = reactive({
  visible: false,
  title: '子任务结果 JSON',
  content: ''
})

const workflowJsonPreview = computed(() => {
  if (!task.workflow_json) return ''
  return JSON.stringify(task.workflow_json, null, 2)
})

const canExecute = computed(() => task.status === 'pending' || task.status === 'fail' || task.status === 'cancelled')
const showProgressPanel = computed(
  () => Boolean(task.id) && (task.status !== 'pending' || Boolean(task.execution_state))
)
const parsedExecutionState = computed(() => {
  const raw = task.execution_state
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
})

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}

function getPrompts(subtask) {
  return (subtask?.extra?.prompts || []).filter((text) => String(text || '').trim())
}

function hasPrompt(subtask) {
  return getPrompts(subtask).length > 0
}

function openPromptPreview(text, title) {
  previewDialog.title = title || 'Markdown 预览'
  previewDialog.html = renderMarkdown(text || '')
  previewDialog.visible = true
}

function openResultMarkdown(text) {
  previewDialog.title = '子任务结果详情'
  previewDialog.html = renderMarkdown(text || '')
  previewDialog.visible = true
}

function hasResult(subtask) {
  return Boolean(subtask?.result && Object.keys(subtask.result).length)
}

function hasRawOutput(subtask) {
  return Boolean(subtask?.result?.raw_output && String(subtask.result.raw_output).trim())
}

function getRawOutputPreview(subtask) {
  const text = String(subtask?.result?.raw_output || '').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  return text.length > 220 ? `${text.slice(0, 220)}...` : text
}

function getStructuredResultEntries(subtask) {
  const entries = Object.entries(subtask?.result || {})
  return entries.filter(([key]) => key !== 'raw_output')
}

function formatResultValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value, null, 2)
}

function openResultJson(subtask) {
  resultJsonDialog.title = '子任务结果 JSON'
  resultJsonDialog.content = JSON.stringify(subtask?.result || {}, null, 2)
  resultJsonDialog.visible = true
}

function getGeneratedImages(subtask) {
  const items = Array.isArray(subtask?.generated_images) ? subtask.generated_images : []
  return [...items].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
}

function getPhotoUrls(subtask) {
  const items = Array.isArray(subtask?.photos) ? subtask.photos : []
  return items.map((item) => item.url).filter(Boolean)
}

function getGeneratedImageUrls(subtask) {
  return getGeneratedImages(subtask).map((item) => item.url).filter(Boolean)
}

async function loadData() {
  loading.value = true
  try {
    const result = await fetchTask(route.params.id)
    Object.assign(task, result)
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleExecute() {
  if (executing.value) return
  try {
    await ElMessageBox.confirm(
      `确认执行任务「${task.title}」的 ComfyUI 工作流？`,
      '执行确认',
      { confirmButtonText: '执行', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  executing.value = true
  try {
    task.status = 'running'
    await nextTick()
    await executeTask(task.id)
    await loadData()
  } catch (error) {
    task.status = 'fail'
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '执行失败')
  } finally {
    executing.value = false
  }
}

async function handleCancel() {
  if (cancelling.value || !task.id) return
  try {
    await ElMessageBox.confirm(
      `确认取消任务「${task.title}」当前执行？`,
      '取消执行',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' }
    )
  } catch {
    return
  }

  cancelling.value = true
  try {
    await cancelExecutionTask(task.id)
    task.status = 'cancelled'
    ElMessage.success('已发送取消请求')
    await loadData()
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '取消执行失败')
  } finally {
    cancelling.value = false
  }
}

async function handleDelete() {
  const subtaskCount = task.subtasks?.length || 0
  try {
    await ElMessageBox.confirm(
      `删除任务后，将同步删除其下 ${subtaskCount} 个子任务。该操作不可恢复。`,
      '高风险操作',
      {
        type: 'error',
        customClass: 'danger-delete-box',
        confirmButtonText: '删除任务',
        cancelButtonText: '取消'
      }
    )
    deleting.value = true
    await deleteTask(task.id)
    ElMessage.success('任务已删除')
    router.replace('/')
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  } finally {
    deleting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-card {
  animation: rise 0.35s ease;
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

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.workflow-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-top: 14px;
  border: 1px solid #b3d4f5;
  border-radius: 10px;
  background: #f0f8ff;
  font-size: 13px;
  color: #1a3f6f;
  flex-wrap: wrap;
}

.workflow-banner--empty {
  border-color: #f0c8a0;
  background: #fffbf5;
  color: #8a5c20;
}

.workflow-icon {
  font-size: 18px;
  color: #409eff;
  flex-shrink: 0;
}

.workflow-label {
  font-weight: 600;
}

.detail-progress {
  margin-top: 12px;
}

.section-title {
  margin: 20px 0 12px;
}

.subtask-card {
  margin-bottom: 12px;
  border: 1px solid #d9e7fb;
  background: linear-gradient(180deg, #fbfdff 0%, #f6faff 100%);
}

.result-panel {
  margin-top: 10px;
  border: 1px solid #dbe8fc;
  background: #fff;
  border-radius: 10px;
  padding: 10px;
}

.result-title {
  font-size: 12px;
  font-weight: 600;
  color: #496386;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}

.raw-output-card {
  border: 1px solid #dce8fb;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  padding: 10px;
}

.raw-output-title {
  font-size: 12px;
  font-weight: 600;
  color: #4b6488;
  margin-bottom: 6px;
}

.raw-output-preview {
  font-size: 13px;
  line-height: 1.6;
  color: #273f63;
  margin-bottom: 6px;
}

.result-kv-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.result-kv-item {
  border: 1px solid #dfebfb;
  border-radius: 8px;
  background: #fff;
  padding: 8px;
}

.result-kv-key {
  font-size: 12px;
  font-weight: 600;
  color: #526989;
  margin-bottom: 6px;
}

.result-kv-value {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: #1f3559;
  white-space: pre-wrap;
  word-break: break-word;
}

.prompt-list {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.prompt-item {
  border: 1px solid #dce7f7;
  border-radius: 10px;
  background: #fff;
  padding: 8px 10px;
}

.prompt-label {
  font-size: 12px;
  color: #4a6283;
  margin-bottom: 6px;
  font-weight: 600;
}

.prompt-snippet {
  color: #2a3f62;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.photo-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.photo-card {
  border: 1px solid #dde8f9;
  border-radius: 8px;
  padding: 6px;
  background: #fff;
  height: 188px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  overflow: hidden;
  background: #f2f6ff;
}

.generated-section {
  margin-top: 10px;
  border-top: 1px dashed #d8e6fb;
  padding-top: 10px;
}

.generated-title {
  font-size: 12px;
  font-weight: 700;
  color: #3e5e88;
  margin-bottom: 8px;
}

.generated-photo-card {
  position: relative;
}

.sort-chip {
  position: absolute;
  right: 10px;
  bottom: 10px;
  font-size: 11px;
  color: #fff;
  background: rgba(17, 24, 39, 0.78);
  border-radius: 999px;
  padding: 1px 6px;
}

.preview-dialog-body {
  max-height: 66vh;
  overflow: auto;
  padding: 4px;
}

.result-json-dialog {
  margin: 0;
  max-height: 66vh;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
  color: #1f3559;
  background: #f7faff;
  border: 1px solid #dce8fb;
  border-radius: 8px;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
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

@media (max-width: 768px) {
  .header-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .photo-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .prompt-list {
    grid-template-columns: 1fr;
  }

  .result-kv-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 769px) and (max-width: 1180px) {
  .photo-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
