<template>
  <div class="comfyui-embed">
    <iframe
      :src="comfyuiUrl"
      class="comfyui-frame"
      frameborder="0"
      allow="clipboard-read; clipboard-write"
      title="ComfyUI 编辑器"
    />
  </div>
</template>

<script setup>
const comfyuiUrl = import.meta.env.VITE_COMFYUI_EMBED_URL || 'http://34.42.194.164:8189'
</script>

<style scoped>
.comfyui-embed {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.comfyui-frame {
  width: 100%;
  flex: 1;
  border: none;
  display: block;
  min-height: 0;
}
</style>
