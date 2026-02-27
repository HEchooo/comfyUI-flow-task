<template>
  <el-card class="page-card">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">工作流</div>
          <div class="page-subtitle">维护可复用工作流并快速生成任务</div>
        </div>
        <el-button type="primary" :disabled="loading" @click="$router.push('/dashboard/templates/new')">新建工作流</el-button>
      </div>
    </template>

    <el-table :data="rows" v-loading="loading" border class="task-table">
      <el-table-column prop="id" label="工作流ID" min-width="260" />
      <el-table-column prop="title" label="工作流名称" min-width="180" />
      <el-table-column prop="subtask_count" label="子任务数" width="100" />
      <el-table-column prop="created_at" label="创建时间" min-width="200">
        <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="scope">
          <el-button
            link
            type="primary"
            :loading="creatingTaskFromTemplateId === scope.row.id"
            :disabled="loading || creatingTaskFromTemplateId === scope.row.id || deletingTemplateId === scope.row.id"
            @click="handleCreateTask(scope.row)"
          >
            创建任务
          </el-button>
          <el-button
            link
            :disabled="loading || creatingTaskFromTemplateId === scope.row.id || deletingTemplateId === scope.row.id"
            @click="$router.push(`/dashboard/templates/${scope.row.id}/edit`)"
          >
            编辑
          </el-button>
          <el-button
            link
            type="danger"
            :loading="deletingTemplateId === scope.row.id"
            :disabled="loading || deletingTemplateId === scope.row.id || creatingTaskFromTemplateId === scope.row.id"
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        @current-change="onPageChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createTaskFromTemplate, deleteTaskTemplate, fetchTaskTemplates } from '../api/templates'
import { isDuplicateRequestError } from '../api/http'

const router = useRouter()
const loading = ref(false)
const rows = ref([])
const creatingTaskFromTemplateId = ref('')
const deletingTemplateId = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

async function loadTemplates() {
  loading.value = true
  try {
    const result = await fetchTaskTemplates({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    rows.value = result.items
    pagination.total = result.total
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '工作流查询失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(page) {
  pagination.page = page
  loadTemplates()
}

async function handleCreateTask(row) {
  try {
    creatingTaskFromTemplateId.value = row.id
    const created = await createTaskFromTemplate(row.id, {})
    ElMessage.success('已从工作流创建任务')
    router.push(`/dashboard/tasks/${created.id}/edit`)
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '创建任务失败')
  } finally {
    creatingTaskFromTemplateId.value = ''
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除工作流「${row.title}」？`, '删除工作流', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    deletingTemplateId.value = row.id
    await deleteTaskTemplate(row.id)
    ElMessage.success('工作流已删除')
    if (rows.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    await loadTemplates()
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除工作流失败')
    }
  } finally {
    deletingTemplateId.value = ''
  }
}

onMounted(loadTemplates)
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
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.task-table {
  border-radius: 12px;
  overflow: hidden;
}

.pagination {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
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
