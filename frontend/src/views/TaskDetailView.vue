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
          <el-button type="danger" plain :disabled="!task.id" @click="handleDelete">删除</el-button>
          <el-button type="primary" @click="$router.push(`/tasks/${task.id}/edit`)" :disabled="!task.id">编辑</el-button>
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
          <div class="result-title">子任务结果 JSON</div>
          <pre class="result-json">{{ formatResult(item.result) }}</pre>
        </div>

        <div v-if="hasPrompt(item)" class="prompt-list">
          <div class="prompt-item" v-for="(prompt, idx) in getPrompts(item)" :key="`${item.id}-prompt-${idx}`">
            <div class="prompt-label">提示词 {{ idx + 1 }}</div>
            <div class="prompt-snippet">{{ prompt }}</div>
            <el-button text type="primary" @click="openPromptPreview(prompt, `子任务提示词 ${idx + 1}`)">Markdown 预览</el-button>
          </div>
        </div>

        <div class="photo-grid">
          <div class="photo-card" v-for="photo in item.photos" :key="photo.id">
            <img :src="photo.url" alt="photo" />
          </div>
        </div>
      </el-card>
    </template>

    <el-dialog v-model="previewDialog.visible" :title="previewDialog.title" width="min(780px, 92vw)" append-to-body>
      <div class="markdown-body preview-dialog-body" v-if="previewDialog.html" v-html="previewDialog.html"></div>
      <el-empty v-else description="暂无内容" />
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteTask, fetchTask } from '../api/tasks'
import { renderMarkdown } from '../utils/markdown'
import { taskStatusType } from '../utils/status'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const task = reactive({})
const previewDialog = reactive({
  visible: false,
  title: 'Markdown 预览',
  html: ''
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

function hasResult(subtask) {
  return Boolean(subtask?.result && Object.keys(subtask.result).length)
}

function formatResult(result) {
  return JSON.stringify(result, null, 2)
}

async function loadData() {
  loading.value = true
  try {
    const result = await fetchTask(route.params.id)
    Object.assign(task, result)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
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
    await deleteTask(task.id)
    ElMessage.success('任务已删除')
    router.replace('/')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
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
  margin-bottom: 6px;
}

.result-json {
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
}

.photo-card img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: 6px;
}

.preview-dialog-body {
  max-height: 66vh;
  overflow: auto;
  padding: 4px;
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
}

@media (min-width: 769px) and (max-width: 1180px) {
  .photo-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
