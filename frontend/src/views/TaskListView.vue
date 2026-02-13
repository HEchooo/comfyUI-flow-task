<template>
  <el-card class="page-card">
    <template #header>
      <div class="header-row">
        <div>
          <div class="page-title">任务列表</div>
          <div class="page-subtitle">查看、检索并管理任务</div>
        </div>
        <div class="head-actions">
          <el-button @click="$router.push('/templates')">工作流</el-button>
          <el-button type="primary" @click="$router.push('/tasks/new')">新建任务</el-button>
        </div>
      </div>
    </template>

    <div class="filters">
      <el-input v-model="filters.taskId" placeholder="按 task_id 查询" clearable class="filter-item" />
      <el-select v-model="filters.status" placeholder="状态筛选" clearable class="status-filter">
        <el-option v-for="item in TASK_STATUS_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" :loading="loading" :disabled="loading" @click="loadTasks">查询</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border class="task-table">
      <el-table-column prop="id" label="任务ID" min-width="250" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="scope">
          <el-tag :type="taskStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subtask_count" label="子任务数" width="100" />
      <el-table-column prop="created_at" label="创建时间" min-width="200">
        <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="scope">
          <el-button link type="primary" :disabled="loading || deletingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}`)">详情</el-button>
          <el-button link :disabled="loading || deletingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}/edit`)">编辑</el-button>
          <el-button
            link
            type="danger"
            :loading="deletingTaskId === scope.row.id"
            :disabled="loading || deletingTaskId === scope.row.id"
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
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteTask, fetchTasks } from '../api/tasks'
import { isDuplicateRequestError } from '../api/http'
import { TASK_STATUS_OPTIONS, taskStatusType } from '../utils/status'
const loading = ref(false)
const rows = ref([])
const deletingTaskId = ref('')

const filters = reactive({
  taskId: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

async function loadTasks() {
  loading.value = true
  try {
    const result = await fetchTasks({
      task_id: filters.taskId || undefined,
      status: filters.status || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    rows.value = result.items
    pagination.total = result.total
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '任务查询失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(page) {
  pagination.page = page
  loadTasks()
}

async function handleDelete(row) {
  const subtaskCount = row.subtask_count || 0
  try {
    await ElMessageBox.confirm(
      `删除任务「${row.title}」后，将同步删除其下 ${subtaskCount} 个子任务。该操作不可恢复。`,
      '高风险操作',
      {
        type: 'error',
        customClass: 'danger-delete-box',
        confirmButtonText: '删除任务',
        cancelButtonText: '取消'
      }
    )

    deletingTaskId.value = row.id
    await deleteTask(row.id)
    ElMessage.success('任务已删除')
    if (rows.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    await loadTasks()
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  } finally {
    deletingTaskId.value = ''
  }
}

onMounted(loadTasks)
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

.head-actions {
  display: flex;
  gap: 8px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
  padding: 12px;
  border-radius: 12px;
  background: #f4f8ff;
}

.filter-item {
  width: min(320px, 100%);
}

.status-filter {
  width: 180px;
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

  .filter-item {
    width: 100%;
  }

  .status-filter {
    width: 100%;
  }
}
</style>
