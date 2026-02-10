<template>
  <div class="photo-input">
    <div class="row">
      <el-input v-model="urlDraft" placeholder="粘贴 imgUrl 后点击添加" clearable />
      <el-button type="primary" @click="addUrl">添加URL</el-button>
    </div>

    <div class="row">
      <el-upload
        :show-file-list="false"
        :http-request="customUpload"
        accept="image/*"
        :before-upload="beforeUpload"
        multiple
      >
        <el-button>选择本地图片</el-button>
      </el-upload>
    </div>

    <div
      class="paste-zone"
      contenteditable="true"
      data-placeholder="Ctrl + V 粘贴图片"
      @paste="onPaste"
      @input="clearPasteBox"
    ></div>

    <div class="photo-grid">
      <div class="photo-card" v-for="(item, index) in localPhotos" :key="`${item.local_preview_url || item.url}-${index}`">
        <button class="thumb-btn" type="button" @click="openPreview(item.url)">
          <img :src="item.url" alt="photo" />
        </button>
        <el-button size="small" type="danger" plain @click="removePhoto(index)">删除</el-button>
      </div>
    </div>

    <el-dialog v-model="previewVisible" width="min(880px, 92vw)" append-to-body>
      <img class="preview-image" :src="previewUrl" alt="preview" />
    </el-dialog>
  </div>
</template>

<script setup>
import { onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  maxImages: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['update:modelValue'])

const urlDraft = ref('')
const localPhotos = ref([])
const previewVisible = ref(false)
const previewUrl = ref('')
const createdBlobUrls = new Set()

watch(
  () => props.modelValue,
  (value) => {
    localPhotos.value = (value || []).map((item) => ({ ...item }))
  },
  { immediate: true, deep: true }
)

function syncAndEmit() {
  localPhotos.value = localPhotos.value.map((item, i) => ({ ...item, sort_order: i }))
  emit('update:modelValue', localPhotos.value)
}

function ensureCapacity() {
  if (localPhotos.value.length >= props.maxImages) {
    ElMessage.error(`最多允许 ${props.maxImages} 张图片`)
    return false
  }
  return true
}

function createPendingEntry(file, sourceType) {
  const preview = URL.createObjectURL(file)
  createdBlobUrls.add(preview)
  return {
    source_type: sourceType,
    url: preview,
    object_key: null,
    upload_state: 'pending',
    raw_file: file,
    local_preview_url: preview,
    sort_order: localPhotos.value.length
  }
}

function addUrl() {
  const url = urlDraft.value.trim()
  if (!url) return
  if (!ensureCapacity()) return

  localPhotos.value.push({
    source_type: 'img_url',
    url,
    object_key: null,
    upload_state: 'uploaded',
    sort_order: localPhotos.value.length
  })
  urlDraft.value = ''
  syncAndEmit()
}

function beforeUpload(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片不能超过 10MB')
    return false
  }
  return true
}

function customUpload({ file, onSuccess, onError }) {
  try {
    if (!ensureCapacity()) {
      if (onError) onError(new Error('capacity limit reached'))
      return
    }
    localPhotos.value.push(createPendingEntry(file, 'upload'))
    syncAndEmit()
    if (onSuccess) onSuccess({}, file)
  } catch (error) {
    if (onError) onError(error)
    ElMessage.error('添加失败')
  }
}

function clearPasteBox(event) {
  event.target.textContent = ''
}

function onPaste(event) {
  event.preventDefault()
  event.target.textContent = ''

  const items = event.clipboardData?.items || []
  for (const item of items) {
    if (!item.type.startsWith('image/')) continue
    if (!ensureCapacity()) return

    const file = item.getAsFile()
    if (!file) continue
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.error('粘贴图片不能超过 10MB')
      continue
    }

    localPhotos.value.push(createPendingEntry(file, 'paste'))
  }
  syncAndEmit()
}

function removePhoto(index) {
  const removed = localPhotos.value.splice(index, 1)[0]
  if (removed?.local_preview_url?.startsWith('blob:')) {
    URL.revokeObjectURL(removed.local_preview_url)
    createdBlobUrls.delete(removed.local_preview_url)
  }
  syncAndEmit()
}

function openPreview(url) {
  previewUrl.value = url
  previewVisible.value = true
}

onUnmounted(() => {
  for (const url of createdBlobUrls) {
    URL.revokeObjectURL(url)
  }
  createdBlobUrls.clear()
})
</script>

<style scoped>
.photo-input {
  padding: 12px;
  border: 1px solid #d8e7fb;
  border-radius: 12px;
  background: linear-gradient(180deg, #fbfdff 0%, #f5faff 100%);
}

.row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.paste-zone {
  min-height: 42px;
  border: 1px solid #d5e5ff;
  border-radius: 10px;
  padding: 8px;
  background: #fff;
  margin-bottom: 12px;
  color: #375178;
  outline: none;
  line-height: 24px;
}

.paste-zone:empty::before {
  content: attr(data-placeholder);
  color: #95a5bd;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.photo-card {
  border: 1px solid #dfe9f8;
  border-radius: 10px;
  padding: 8px;
  background: #fff;
  box-shadow: 0 8px 16px rgba(18, 51, 102, 0.06);
}

.thumb-btn {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0;
  cursor: zoom-in;
  margin-bottom: 6px;
}

.thumb-btn img {
  width: 100%;
  height: 88px;
  object-fit: cover;
  border-radius: 6px;
}

.preview-image {
  width: 100%;
  max-height: 76vh;
  object-fit: contain;
}

@media (max-width: 1200px) {
  .photo-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .photo-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .photo-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
