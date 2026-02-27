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

    <el-table
      :data="rows"
      v-loading="loading"
      border
      class="task-table"
      :row-key="getRowKey"
      :expand-row-keys="expandedRowKeys"
      @expand-change="onExpandChange"
    >
      <el-table-column type="expand" width="44">
        <template #default="scope">
          <div class="row-progress-wrap">
            <ExecutionProgress
              inline
              :task-id="String(scope.row.id)"
              :task-status="String(scope.row.status || '')"
              :initial-state="scope.row.execution_state"
              :active="isExpanded(scope.row.id)"
            />
          </div>
        </template>
      </el-table-column>
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
      <el-table-column label="操作" width="360" fixed="right">
        <template #default="scope">
          <el-button link type="primary" :disabled="loading || deletingTaskId === scope.row.id || cancellingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}`)">详情</el-button>
          <el-button link :disabled="loading || deletingTaskId === scope.row.id || cancellingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}/edit`)">编辑</el-button>
          <el-button
            v-if="scope.row.status === 'running'"
            link
            type="warning"
            :disabled="loading || cancellingTaskId === scope.row.id"
            :loading="cancellingTaskId === scope.row.id"
            @click="handleCancel(scope.row)"
          >
            取消执行
          </el-button>
          <el-tooltip
            v-else-if="canExecute(scope.row)"
            :content="!scope.row.has_workflow ? '请先上传工作流' : '执行 ComfyUI 工作流'"
            placement="top"
          >
            <span>
                <el-button
                  link
                  type="success"
                  :disabled="loading || !scope.row.has_workflow || executingTaskId === scope.row.id || cancellingTaskId === scope.row.id"
                  :loading="executingTaskId === scope.row.id"
                  @click="handleExecute(scope.row)"
                >
                  执行
                </el-button>
            </span>
          </el-tooltip>
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

  <ExecuteEndpointDialog
    v-model="endpointDialogVisible"
    :task-title="pendingExecuteTaskTitle"
    :submitting="endpointDialogSubmitting"
    @confirm="handleConfirmExecute"
  />

</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import ExecutionProgress from '../components/ExecutionProgress.vue'
import ExecuteEndpointDialog from '../components/ExecuteEndpointDialog.vue'
import { deleteTask, fetchTasks } from '../api/tasks'
import { cancelExecutionTask, executeTask } from '../api/execution'
import { isDuplicateRequestError } from '../api/http'
import { TASK_STATUS_OPTIONS, taskStatusType } from '../utils/status'

const loading = ref(false)
const rows = ref([])
const deletingTaskId = ref('')
const executingTaskId = ref('')
const cancellingTaskId = ref('')
const expandedRowKeys = ref([])
const endpointDialogVisible = ref(false)
const endpointDialogSubmitting = ref(false)
const pendingExecuteTaskId = ref('')
const pendingExecuteTaskTitle = ref('')

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

function getRowKey(row) {
  return String(row.id)
}

function isExpanded(taskId) {
  const key = String(taskId)
  return expandedRowKeys.value.includes(key)
}

function openProgress(taskId) {
  const key = String(taskId)
  expandedRowKeys.value = [key]
}

function canExecute(row) {
  return row.status === 'pending' || row.status === 'fail' || row.status === 'cancelled'
}

function onExpandChange(row, expandedRows) {
  const rowId = String(row.id)
  const expanded = expandedRows.some((item) => String(item.id) === rowId)
  if (expanded) {
    expandedRowKeys.value = [rowId]
    return
  }
  expandedRowKeys.value = expandedRowKeys.value.filter((key) => key !== rowId)
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

async function handleExecute(row) {
  if (executingTaskId.value || cancellingTaskId.value) {
    return
  }
  pendingExecuteTaskId.value = String(row.id)
  pendingExecuteTaskTitle.value = String(row.title || '')
  endpointDialogVisible.value = true
}

async function handleConfirmExecute(endpoint) {
  if (!pendingExecuteTaskId.value) return
  const taskId = pendingExecuteTaskId.value
  const row = rows.value.find((item) => String(item.id) === taskId)
  if (!row) {
    ElMessage.warning('任务不存在或列表已刷新，请重试')
    return
  }

  executingTaskId.value = row.id
  endpointDialogSubmitting.value = true
  let executeSuccess = false
  try {
    openProgress(row.id)
    row.status = 'running'
    await nextTick()
    await executeTask(row.id, {
      server_ip: endpoint.server_ip,
      port: endpoint.port
    })
    await loadTasks()
    executeSuccess = true
  } catch (error) {
    row.status = 'fail'
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '执行失败')
  } finally {
    executingTaskId.value = ''
    endpointDialogSubmitting.value = false
    if (executeSuccess) {
      endpointDialogVisible.value = false
      pendingExecuteTaskId.value = ''
      pendingExecuteTaskTitle.value = ''
    }
  }
}

async function handleCancel(row) {
  if (cancellingTaskId.value) return
  try {
    await ElMessageBox.confirm(
      `确认取消任务「${row.title}」当前执行？`,
      '取消执行',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' }
    )
  } catch {
    return
  }

  cancellingTaskId.value = row.id
  try {
    await cancelExecutionTask(row.id)
    row.status = 'cancelled'
    openProgress(row.id)
    ElMessage.success('已发送取消请求')
    await loadTasks()
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '取消执行失败')
  } finally {
    cancellingTaskId.value = ''
  }
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

.row-progress-wrap {
  padding: 4px 6px;
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
