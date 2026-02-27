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
      <el-table-column label="定时执行" min-width="180">
        <template #default="scope">
          <el-tag v-if="scope.row.schedule_enabled" type="success">
            {{ formatSchedule(scope.row) }}
          </el-tag>
          <el-tag v-else type="info">未启用</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subtask_count" label="子任务数" width="100" />
      <el-table-column prop="created_at" label="创建时间" min-width="200">
        <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="430" fixed="right">
        <template #default="scope">
          <el-button link type="primary" :disabled="loading || deletingTaskId === scope.row.id || cancellingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}`)">详情</el-button>
          <el-button link :disabled="loading || deletingTaskId === scope.row.id || cancellingTaskId === scope.row.id" @click="$router.push(`/tasks/${scope.row.id}/edit`)">编辑</el-button>
          <el-button
            link
            type="warning"
            v-if="scope.row.status !== 'success'"
            :disabled="loading || deletingTaskId === scope.row.id || cancellingTaskId === scope.row.id"
            @click="openScheduleDialog(scope.row)"
          >
            定时
          </el-button>
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
  <el-dialog
    v-model="scheduleDialogVisible"
    title="快速设置定时"
    width="min(640px, 92vw)"
    :close-on-click-modal="false"
  >
    <div class="schedule-dialog-shell">
      <div class="schedule-dialog-head">
        <div>
          <div class="schedule-dialog-title">任务定时策略</div>
          <div class="schedule-dialog-sub">支持自动调度与固定端口两种执行模式</div>
        </div>
        <el-form-item label="启用定时" class="dialog-switch-item">
          <el-switch v-model="scheduleForm.schedule_enabled" />
        </el-form-item>
      </div>
      <transition name="dialog-fade">
        <el-form v-if="scheduleForm.schedule_enabled" label-position="top" class="schedule-dialog-form">
          <el-form-item label="执行日期" required>
            <el-date-picker
              v-model="scheduleForm.schedule_at"
              type="datetime"
              format="YYYY-MM-DD HH:mm"
              placeholder="选择年月日时分"
              class="dialog-full"
            />
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">
                自动调度
                <el-tooltip content="自动调度：触发时自动选择空闲或排队最少的端口，无需手动指定端口。">
                  <el-text class="help-icon">?</el-text>
                </el-tooltip>
              </span>
            </template>
            <el-switch v-model="scheduleForm.schedule_auto_dispatch" />
          </el-form-item>
          <el-form-item v-if="!scheduleForm.schedule_auto_dispatch" label="固定端口" required>
            <el-select
              v-model="scheduleForm.schedule_port"
              :loading="loadingScheduleSettings"
              placeholder="选择端口"
              class="dialog-full"
            >
              <el-option v-for="port in schedulePorts" :key="port" :label="`:${port}`" :value="port" />
            </el-select>
          </el-form-item>
          <div v-else class="auto-dispatch-hint">系统将在触发时自动选择最优端口</div>
          <div class="schedule-server-tip">当前服务器: {{ scheduleServerIp || '-' }}</div>
        </el-form>
      </transition>
    </div>
    <template #footer>
      <el-button @click="scheduleDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="savingSchedule" @click="saveQuickSchedule">保存</el-button>
    </template>
  </el-dialog>

</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import ExecutionProgress from '../components/ExecutionProgress.vue'
import ExecuteEndpointDialog from '../components/ExecuteEndpointDialog.vue'
import { deleteTask, fetchTasks, patchTask } from '../api/tasks'
import { cancelExecutionTask, executeTask } from '../api/execution'
import { isDuplicateRequestError } from '../api/http'
import { fetchComfyuiSettings } from '../api/settings'
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
const scheduleDialogVisible = ref(false)
const savingSchedule = ref(false)
const loadingScheduleSettings = ref(false)
const scheduleTaskId = ref('')
const scheduleServerIp = ref('')
const schedulePorts = ref([])
const scheduleForm = reactive({
  schedule_enabled: false,
  schedule_at: null,
  schedule_auto_dispatch: true,
  schedule_port: null
})

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

function formatSchedule(row) {
  const when = row.schedule_at ? formatTime(row.schedule_at) : (row.schedule_time || '--')
  if (row.schedule_auto_dispatch) {
    return `${when} 自动调度`
  }
  if (row.schedule_port) {
    return `${when} :${row.schedule_port}`
  }
  return `${when} 未选端口`
}

function defaultScheduleAt() {
  const value = new Date()
  value.setSeconds(0, 0)
  value.setMinutes(value.getMinutes() + 5)
  return value
}

function scheduleAtFromLegacyTime(value) {
  const raw = String(value || '').trim()
  if (!raw) return null
  const parts = raw.split(':').map((item) => Number(item))
  if (parts.length !== 2 || Number.isNaN(parts[0]) || Number.isNaN(parts[1])) return null
  const dt = new Date()
  dt.setSeconds(0, 0)
  dt.setHours(parts[0], parts[1], 0, 0)
  return dt
}

async function loadScheduleSettings() {
  loadingScheduleSettings.value = true
  try {
    const result = await fetchComfyuiSettings()
    scheduleServerIp.value = result.server_ip || ''
    schedulePorts.value = Array.isArray(result.ports) ? result.ports : []
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    scheduleServerIp.value = ''
    schedulePorts.value = []
    ElMessage.error(error?.response?.data?.detail || '加载端口设置失败')
  } finally {
    loadingScheduleSettings.value = false
  }
}

async function openScheduleDialog(row) {
  if (String(row.status || '') === 'success') {
    return
  }
  scheduleTaskId.value = String(row.id)
  scheduleForm.schedule_enabled = Boolean(row.schedule_enabled)
  scheduleForm.schedule_at = row.schedule_at
    ? new Date(row.schedule_at)
    : (scheduleAtFromLegacyTime(row.schedule_time) || defaultScheduleAt())
  scheduleForm.schedule_auto_dispatch = row.schedule_enabled
    ? Boolean(row.schedule_auto_dispatch)
    : true
  scheduleForm.schedule_port = Number.isInteger(row.schedule_port) ? row.schedule_port : null
  if (scheduleForm.schedule_auto_dispatch) {
    scheduleForm.schedule_port = null
  }
  await loadScheduleSettings()
  scheduleDialogVisible.value = true
}

async function saveQuickSchedule() {
  if (!scheduleTaskId.value) return
  if (savingSchedule.value) return
  if (scheduleForm.schedule_enabled) {
    if (!scheduleForm.schedule_at) {
      ElMessage.warning('请设置执行日期')
      return
    }
    if (!scheduleForm.schedule_auto_dispatch && !scheduleForm.schedule_port) {
      ElMessage.warning('请选择固定端口，或开启自动调度')
      return
    }
  }

  savingSchedule.value = true
  try {
    await patchTask(scheduleTaskId.value, {
      schedule_enabled: Boolean(scheduleForm.schedule_enabled),
      schedule_at: scheduleForm.schedule_enabled && scheduleForm.schedule_at
        ? new Date(scheduleForm.schedule_at).toISOString()
        : null,
      schedule_auto_dispatch: scheduleForm.schedule_enabled
        ? Boolean(scheduleForm.schedule_auto_dispatch)
        : false,
      schedule_port: scheduleForm.schedule_enabled && !scheduleForm.schedule_auto_dispatch && scheduleForm.schedule_port
        ? Number(scheduleForm.schedule_port)
        : null
    })
    ElMessage.success('定时设置已保存')
    scheduleDialogVisible.value = false
    await loadTasks()
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '定时设置保存失败')
  } finally {
    savingSchedule.value = false
  }
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

.dialog-full {
  width: 100%;
}

.schedule-dialog-shell {
  padding: 12px;
  border: 1px solid #d6e7ff;
  border-radius: 14px;
  background: linear-gradient(160deg, #fbfdff 0%, #f2f8ff 56%, #eef9f6 100%);
}

.schedule-dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.schedule-dialog-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a4e97;
}

.schedule-dialog-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #6b84a8;
}

.dialog-switch-item {
  margin-bottom: 0;
}

.schedule-dialog-form {
  margin-top: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #cbe1ff;
  background: rgba(255, 255, 255, 0.72);
}

.schedule-server-tip {
  margin-top: 2px;
  font-size: 12px;
  color: #5f7498;
}

.label-with-help {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.help-icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #4f79b3;
  font-size: 11px;
  font-weight: 700;
  cursor: help;
}

.auto-dispatch-hint {
  margin-bottom: 8px;
  font-size: 12px;
  color: #2f6f57;
  background: rgba(53, 166, 127, 0.14);
  border: 1px solid rgba(53, 166, 127, 0.3);
  border-radius: 999px;
  padding: 6px 10px;
  width: fit-content;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: all 0.24s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
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

  .schedule-dialog-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .dialog-switch-item {
    width: 100%;
  }
}
</style>
