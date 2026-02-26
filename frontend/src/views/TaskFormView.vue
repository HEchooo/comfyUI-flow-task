<template>
  <el-card class="page-card">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">{{ isEdit ? '编辑任务' : '创建任务' }}</div>
          <div class="page-subtitle">配置子任务账号、发布时间和图片</div>
        </div>
        <el-button @click="$router.push('/')">返回列表</el-button>
      </div>
    </template>

    <el-form label-width="100px" :model="form" class="form-wrap">
      <el-form-item label="标题">
        <el-input v-model="form.title" maxlength="200" show-word-limit />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>

      <el-form-item v-if="!isEdit" label="应用工作流">
        <div class="template-tools">
          <el-select v-model="selectedTemplateId" placeholder="选择工作流" clearable class="template-select">
            <el-option v-for="item in templateOptions" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
          <el-button :loading="applyingTemplate" :disabled="!selectedTemplateId || applyingTemplate" @click="applyTemplate">填充工作流</el-button>
          <el-button text type="primary" @click="$router.push('/templates')">管理工作流</el-button>
        </div>
      </el-form-item>

      <el-form-item label="ComfyUI 工作流">
        <WorkflowUpload v-model="form.workflow_json" v-model:filename="form.workflow_filename" />
      </el-form-item>

      <div class="subtask-header">
        <h3>子任务</h3>
        <el-button type="primary" plain @click="addSubtask">新增子任务</el-button>
      </div>

      <el-empty v-if="!form.subtasks.length" description="暂无子任务" />

      <el-card class="subtask-card" v-for="(subtask, index) in form.subtasks" :key="index">
        <template #header>
          <div class="header-row compact">
            <span class="subtask-title">子任务 #{{ index + 1 }}</span>
            <el-button type="danger" link @click="removeSubtask(index)">删除</el-button>
          </div>
        </template>

        <el-row :gutter="12">
          <el-col :xs="24" :md="8">
            <el-form-item label="平台" required>
              <el-select v-model="subtask.platform" placeholder="请选择">
                <el-option label="instagram" value="instagram" />
                <el-option label="tiktok" value="tiktok" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="账号名称" required>
              <el-input v-model="subtask.account_name" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="账号编号" required>
              <el-input v-model="subtask.account_no" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :xs="24" :md="8">
            <el-form-item label="发布时间" required>
              <el-date-picker v-model="subtask.publish_at" type="date" placeholder="选择日期" format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="prompts-panel">
          <div class="prompts-title">提示词（支持 Markdown）</div>
          <el-row :gutter="10">
            <el-col :xs="24" :md="12" v-for="promptIndex in 10" :key="promptIndex">
              <el-form-item :label="`提示词 ${promptIndex}`">
                <el-input
                  v-model="subtask.prompts[promptIndex - 1]"
                  type="textarea"
                  :rows="2"
                  :placeholder="`输入提示词 ${promptIndex}`"
                />
                <div class="prompt-actions">
                  <el-button
                    text
                    type="primary"
                    :disabled="!subtask.prompts[promptIndex - 1]?.trim()"
                    @click="openPromptPreview(subtask.prompts[promptIndex - 1], `子任务 #${index + 1} 提示词 ${promptIndex}`)"
                  >
                    Markdown 预览
                  </el-button>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <el-form-item label="照片列表">
          <PhotoInput v-model="subtask.photos" :max-images="10" />
        </el-form-item>
      </el-card>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">{{ isEdit ? '保存修改' : '创建任务' }}</el-button>
      </el-form-item>
    </el-form>

    <el-dialog v-model="previewDialog.visible" :title="previewDialog.title" width="min(780px, 92vw)" append-to-body>
      <div class="markdown-body preview-dialog-body" v-if="previewDialog.html" v-html="previewDialog.html"></div>
      <el-empty v-else description="暂无内容" />
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElLoading, ElMessage } from 'element-plus'

import PhotoInput from '../components/PhotoInput.vue'
import WorkflowUpload from '../components/WorkflowUpload.vue'
import { isDuplicateRequestError } from '../api/http'
import { createTask, fetchTask, patchTask, uploadImageByFile } from '../api/tasks'
import { fetchTaskTemplate, fetchTaskTemplates } from '../api/templates'
import { renderMarkdown } from '../utils/markdown'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const applyingTemplate = ref(false)

const form = reactive({
  title: '',
  description: '',
  workflow_json: null,
  workflow_filename: '',
  subtasks: []
})
const templateOptions = ref([])
const selectedTemplateId = ref('')

const isEdit = computed(() => Boolean(route.params.id))

function createSubtask() {
  return {
    platform: 'instagram',
    account_name: '',
    account_no: '',
    publish_at: null,
    prompts: Array.from({ length: 10 }, () => ''),
    photos: [],
    extra: {}
  }
}

function addSubtask() {
  form.subtasks.push(createSubtask())
}

function removeSubtask(index) {
  form.subtasks.splice(index, 1)
}

async function loadTemplateOptions() {
  try {
    const result = await fetchTaskTemplates({ page: 1, page_size: 100 })
    templateOptions.value = result.items || []
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '加载工作流列表失败')
  }
}

function mapTemplateSubtask(item) {
  return {
    platform: item.platform,
    account_name: item.account_name,
    account_no: item.account_no,
    publish_at: parseDateOnly(item.publish_at),
    prompts: Array.from({ length: 10 }, (_, idx) => item.extra?.prompts?.[idx] || ''),
    photos: [],
    extra: item.extra || {}
  }
}

async function applyTemplate() {
  if (!selectedTemplateId.value || applyingTemplate.value) return
  applyingTemplate.value = true
  try {
    const template = await fetchTaskTemplate(selectedTemplateId.value)
    form.title = template.title
    form.description = template.description || ''
    form.workflow_json = template.workflow_json || null
    form.workflow_filename = ''
    form.subtasks = (template.subtasks || []).map(mapTemplateSubtask)
    if (!form.subtasks.length) {
      addSubtask()
    }
    ElMessage.success('工作流已填充，可继续补充图片后保存任务')
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '应用工作流失败')
  } finally {
    applyingTemplate.value = false
  }
}

const previewDialog = reactive({
  visible: false,
  title: 'Markdown 预览',
  html: ''
})

function openPromptPreview(text, title) {
  previewDialog.title = title || 'Markdown 预览'
  previewDialog.html = renderMarkdown(text || '')
  previewDialog.visible = true
}

function normalizePayload() {
  const formatDateStartOfDay = (value) => {
    if (!value) return null
    const d = new Date(value)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}T00:00:00Z`
  }

  return {
    title: form.title,
    description: form.description,
    workflow_json: form.workflow_json || null,
    workflow_filename: form.workflow_filename || null,
    subtasks: form.subtasks.map((item) => ({
      platform: item.platform,
      account_name: item.account_name,
      account_no: item.account_no,
      publish_at: formatDateStartOfDay(item.publish_at),
      extra: {
        ...(item.extra || {}),
        prompts: Array.from({ length: 10 }, (_, idx) => item.prompts?.[idx] || '')
      },
      photos: item.photos.map((photo, idx) => ({
        source_type: photo.source_type,
        url: photo.url,
        object_key: photo.object_key || null,
        sort_order: idx
      }))
    }))
  }
}

function validateSubtasks() {
  if (!form.subtasks.length) {
    ElMessage.warning('请至少添加一个子任务')
    return false
  }

  for (let i = 0; i < form.subtasks.length; i += 1) {
    const item = form.subtasks[i]
    const idx = i + 1
    if (!item.platform) {
      ElMessage.warning(`子任务 #${idx} 的平台为必填`)
      return false
    }
    if (!item.account_name?.trim()) {
      ElMessage.warning(`子任务 #${idx} 的账号名称为必填`)
      return false
    }
    if (!item.account_no?.trim()) {
      ElMessage.warning(`子任务 #${idx} 的账号编号为必填`)
      return false
    }
    if (!item.publish_at) {
      ElMessage.warning(`子任务 #${idx} 的发布时间为必填`)
      return false
    }
  }
  return true
}

function parseDateOnly(value) {
  if (!value) return null
  const datePart = String(value).slice(0, 10)
  const [y, m, d] = datePart.split('-').map((v) => Number(v))
  if (!y || !m || !d) return new Date(value)
  return new Date(y, m - 1, d)
}

async function uploadPendingPhotos() {
  const pending = []
  form.subtasks.forEach((subtask, subtaskIndex) => {
    subtask.photos.forEach((photo, photoIndex) => {
      if (photo.upload_state === 'pending' && photo.raw_file) {
        pending.push({ subtaskIndex, photoIndex, file: photo.raw_file })
      }
    })
  })

  if (!pending.length) {
    return
  }

  const loading = ElLoading.service({
    lock: true,
    text: `上传中 ${pending.length}`,
    background: 'rgba(255, 255, 255, 0.7)'
  })

  try {
    let cursor = 0
    async function worker() {
      while (cursor < pending.length) {
        const current = pending[cursor]
        cursor += 1

        const uploaded = await uploadImageByFile(current.file)
        const target = form.subtasks[current.subtaskIndex]?.photos?.[current.photoIndex]
        if (!target) continue

        target.url = uploaded.url
        target.object_key = uploaded.object_key
        target.upload_state = 'uploaded'

        if (target.local_preview_url?.startsWith('blob:')) {
          URL.revokeObjectURL(target.local_preview_url)
        }
        delete target.local_preview_url
        delete target.raw_file
      }
    }

    const concurrency = Math.min(4, pending.length)
    await Promise.all(Array.from({ length: concurrency }, () => worker()))
  } finally {
    loading.close()
  }
}

async function loadDetail() {
  if (!isEdit.value) {
    await loadTemplateOptions()
    addSubtask()
    return
  }

  try {
    const data = await fetchTask(route.params.id)
    form.title = data.title
    form.description = data.description || ''
    form.workflow_json = data.workflow_json || null
    form.workflow_filename = data.workflow_filename || ''
    form.subtasks = data.subtasks.map((item) => ({
      platform: item.platform,
      account_name: item.account_name,
      account_no: item.account_no,
      publish_at: parseDateOnly(item.publish_at),
      prompts: Array.from({ length: 10 }, (_, idx) => item.extra?.prompts?.[idx] || ''),
      photos: item.photos || [],
      extra: item.extra || {}
    }))
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '加载任务失败')
  }
}

async function submit() {
  if (submitting.value) return
  if (!form.title.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }
  if (!validateSubtasks()) {
    return
  }

  submitting.value = true
  try {
    await uploadPendingPhotos()
    const payload = normalizePayload()
    let saved
    if (isEdit.value) {
      saved = await patchTask(route.params.id, payload)
      ElMessage.success('任务已更新')
    } else {
      saved = await createTask(payload)
      ElMessage.success('任务已创建')
    }
    router.push(`/tasks/${saved.id}`)
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadDetail)
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

.form-wrap {
  padding: 4px 2px;
}

.template-tools {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-select {
  width: 320px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.header-row.compact {
  padding: 2px 0;
}

.subtask-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.subtask-title {
  font-weight: 700;
  color: #184a90;
}

.subtask-card {
  margin-bottom: 14px;
  border: 1px solid #d9e7fb;
  background: linear-gradient(180deg, #fbfdff 0%, #f6faff 100%);
}

.prompts-panel {
  margin: 8px 0 6px;
  padding: 10px 10px 2px;
  border: 1px dashed #cfe1fb;
  border-radius: 10px;
  background: #f9fcff;
}

.prompts-title {
  font-size: 13px;
  font-weight: 600;
  color: #355985;
  margin-bottom: 8px;
}

.prompt-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
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

  .template-tools {
    flex-wrap: wrap;
  }

  .template-select {
    width: 100%;
  }
}
</style>
