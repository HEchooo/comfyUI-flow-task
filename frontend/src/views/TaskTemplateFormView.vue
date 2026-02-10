<template>
  <el-card class="page-card">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">{{ isEdit ? '编辑工作流' : '新建工作流' }}</div>
          <div class="page-subtitle">工作流仅保存提示词和文本信息，不保存图片</div>
        </div>
        <el-button @click="$router.push('/templates')">返回工作流列表</el-button>
      </div>
    </template>

    <el-form label-width="100px" :model="form" class="form-wrap">
      <el-form-item label="工作流名称">
        <el-input v-model="form.title" maxlength="200" show-word-limit />
      </el-form-item>
      <el-form-item label="工作流描述">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>

      <div class="subtask-header">
        <h3>工作流子任务</h3>
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
      </el-card>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">{{ isEdit ? '保存工作流' : '创建工作流' }}</el-button>
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
import { ElMessage } from 'element-plus'

import { createTaskTemplate, fetchTaskTemplate, patchTaskTemplate } from '../api/templates'
import { renderMarkdown } from '../utils/markdown'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const isEdit = computed(() => Boolean(route.params.id))

const form = reactive({
  title: '',
  description: '',
  subtasks: []
})

const previewDialog = reactive({
  visible: false,
  title: 'Markdown 预览',
  html: ''
})

function createSubtask() {
  return {
    platform: 'instagram',
    account_name: '',
    account_no: '',
    publish_at: null,
    prompts: Array.from({ length: 10 }, () => ''),
    extra: {}
  }
}

function addSubtask() {
  form.subtasks.push(createSubtask())
}

function removeSubtask(index) {
  form.subtasks.splice(index, 1)
}

function openPromptPreview(text, title) {
  previewDialog.title = title || 'Markdown 预览'
  previewDialog.html = renderMarkdown(text || '')
  previewDialog.visible = true
}

function parseDateOnly(value) {
  if (!value) return null
  const datePart = String(value).slice(0, 10)
  const [y, m, d] = datePart.split('-').map((v) => Number(v))
  if (!y || !m || !d) return new Date(value)
  return new Date(y, m - 1, d)
}

function formatDateStartOfDay(value) {
  if (!value) return null
  const d = new Date(value)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}T00:00:00Z`
}

function normalizePayload() {
  return {
    title: form.title,
    description: form.description,
    subtasks: form.subtasks.map((item) => ({
      platform: item.platform,
      account_name: item.account_name,
      account_no: item.account_no,
      publish_at: formatDateStartOfDay(item.publish_at),
      extra: {
        ...(item.extra || {}),
        prompts: Array.from({ length: 10 }, (_, idx) => item.prompts?.[idx] || '')
      }
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

async function loadDetail() {
  if (!isEdit.value) {
    addSubtask()
    return
  }
  try {
    const data = await fetchTaskTemplate(route.params.id)
    form.title = data.title
    form.description = data.description || ''
    form.subtasks = (data.subtasks || []).map((item) => ({
      platform: item.platform,
      account_name: item.account_name,
      account_no: item.account_no,
      publish_at: parseDateOnly(item.publish_at),
      prompts: Array.from({ length: 10 }, (_, idx) => item.extra?.prompts?.[idx] || ''),
      extra: item.extra || {}
    }))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载工作流失败')
  }
}

async function submit() {
  if (!form.title.trim()) {
    ElMessage.warning('工作流名称不能为空')
    return
  }
  if (!validateSubtasks()) {
    return
  }
  submitting.value = true
  try {
    const payload = normalizePayload()
    if (isEdit.value) {
      await patchTaskTemplate(route.params.id, payload)
      ElMessage.success('工作流已更新')
    } else {
      await createTaskTemplate(payload)
      ElMessage.success('工作流已创建')
    }
    router.push('/templates')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存工作流失败')
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
}
</style>
