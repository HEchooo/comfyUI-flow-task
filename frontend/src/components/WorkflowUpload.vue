<template>
  <div class="workflow-upload">
    <!-- Uploaded state -->
    <div v-if="modelValue" class="workflow-info">
      <div class="workflow-info-row">
        <el-icon class="info-icon"><Document /></el-icon>
        <span class="info-filename">{{ displayFilename }}</span>
        <el-tag size="small" type="success">{{ nodeCount }} 个节点</el-tag>
      </div>
      <div class="info-actions">
        <el-button text type="primary" size="small" @click="previewVisible = true">查看 JSON</el-button>
        <el-button text type="danger" size="small" @click="handleRemove">移除</el-button>
      </div>
    </div>

    <!-- Upload zone -->
    <div
      v-else
      class="upload-zone"
      :class="{ 'is-dragover': isDragover, 'is-uploading': uploading }"
      @dragover.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">
        <span v-if="uploading">上传中…</span>
        <span v-else>拖拽 .json 文件到此处，或<em>点击选择</em></span>
      </div>
      <input ref="fileInput" type="file" accept=".json" style="display:none" @change="handleFileChange" />
    </div>

    <!-- JSON preview dialog -->
    <el-dialog v-model="previewVisible" title="工作流 JSON" width="min(820px, 94vw)" append-to-body>
      <pre class="json-preview">{{ jsonPreview }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Upload } from '@element-plus/icons-vue'
import { uploadWorkflow } from '../api/execution'
import { isDuplicateRequestError } from '../api/http'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const isDragover = ref(false)
const uploading = ref(false)
const previewVisible = ref(false)
const uploadedFilename = ref('')
const nodeCount = ref(0)

// When modelValue is set externally (e.g., loaded from server after page refresh),
// derive nodeCount from the JSON keys and show a fallback filename.
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      const count = Object.keys(newVal).length
      nodeCount.value = count
      if (!uploadedFilename.value) {
        uploadedFilename.value = 'workflow.json'
      }
    } else {
      uploadedFilename.value = ''
      nodeCount.value = 0
    }
  },
  { immediate: true }
)

const displayFilename = computed(() => uploadedFilename.value || 'workflow.json')

const jsonPreview = computed(() => {
  if (!props.modelValue) return ''
  return JSON.stringify(props.modelValue, null, 2)
})

function triggerFileInput() {
  if (uploading.value) return
  fileInput.value?.click()
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) upload(file)
  e.target.value = ''
}

function handleDrop(e) {
  isDragover.value = false
  const file = e.dataTransfer.files?.[0]
  if (!file) return
  if (!file.name.endsWith('.json')) {
    ElMessage.error('只支持 .json 文件')
    return
  }
  upload(file)
}

async function upload(file) {
  if (!file.name.endsWith('.json')) {
    ElMessage.error('只支持 .json 文件')
    return
  }
  uploading.value = true
  try {
    const result = await uploadWorkflow(file)
    uploadedFilename.value = result.filename
    nodeCount.value = result.node_count
    emit('update:modelValue', result.workflow_json)
    ElMessage.success(`工作流已上传（${result.node_count} 个节点）`)
  } catch (error) {
    if (isDuplicateRequestError(error)) return
    ElMessage.error(error?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function handleRemove() {
  uploadedFilename.value = ''
  nodeCount.value = 0
  emit('update:modelValue', null)
}
</script>

<style scoped>
.workflow-upload {
  width: 100%;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  border: 2px dashed #c0d4f0;
  border-radius: 10px;
  background: #f8fbff;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  min-height: 90px;
}

.upload-zone:hover,
.upload-zone.is-dragover {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-zone.is-uploading {
  cursor: not-allowed;
  opacity: 0.7;
}

.upload-icon {
  font-size: 28px;
  color: #a0b8d8;
}

.upload-text {
  font-size: 13px;
  color: #6b8ab0;
}

.upload-text em {
  font-style: normal;
  color: #409eff;
}

.workflow-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid #b3d4f5;
  border-radius: 10px;
  background: #f0f8ff;
  flex-wrap: wrap;
}

.workflow-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.info-icon {
  font-size: 18px;
  color: #409eff;
  flex-shrink: 0;
}

.info-filename {
  font-size: 13px;
  color: #1a3f6f;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.json-preview {
  margin: 0;
  max-height: 60vh;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
  color: #1f3559;
  background: #f7faff;
  border: 1px solid #dce8fb;
  border-radius: 8px;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
