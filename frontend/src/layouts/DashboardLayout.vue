<template>
  <div class="dashboard-layout" :class="{ 'sidebar-collapsed': isCollapsed }">
    <AppSidebar :collapsed="isCollapsed" @toggle="toggle" />

    <div class="dashboard-main" :style="{ marginLeft: isCollapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)' }">
      <AppHeader @toggle-sidebar="toggle" />

      <div class="content-stack">
        <!--
          ComfyUI iframe：始终存在且不被任何元素遮挡。
          非 ComfyUI 路由时用 opacity:0 + pointer-events:none 隐藏，
          但浏览器仍然保持其渲染进程，切换时零延迟。
        -->
        <div
          class="comfyui-pane"
          :class="{ 'comfyui-pane--hidden': !isFullscreen }"
        >
          <!-- 首次加载遮罩（仅加载期间显示） -->
          <transition name="fade">
            <div v-if="iframeLoading" class="comfyui-loading">
              <div class="loading-track">
                <div class="loading-fill" :style="{ width: loadingProgress + '%' }" />
              </div>
              <div class="loading-label">ComfyUI 加载中 {{ Math.floor(loadingProgress) }}%</div>
            </div>
          </transition>
          <iframe
            :src="comfyuiUrl"
            class="comfyui-frame"
            frameborder="0"
            allow="clipboard-read; clipboard-write"
            title="ComfyUI 编辑器"
            @load="onIframeLoad"
          />
        </div>

        <!--
          普通页面：非 ComfyUI 路由时正常显示；
          ComfyUI 路由时移出屏幕（translateX），不遮挡 iframe。
        -->
        <main
          class="dashboard-content"
          :class="{ 'dashboard-content--offscreen': isFullscreen }"
        >
          <router-view v-slot="{ Component, route: viewRoute }">
            <transition name="page-fade" mode="out-in">
              <div :key="viewRoute.path" class="page-wrapper">
                <component :is="Component" />
              </div>
            </transition>
          </router-view>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'
import AppHeader from '../components/AppHeader.vue'
import { useSidebar } from '../composables/useSidebar'

const { isCollapsed, toggle } = useSidebar()
const route = useRoute()
const isFullscreen = computed(() => route.name === 'comfyui')
const comfyuiUrl = import.meta.env.VITE_COMFYUI_EMBED_URL || 'http://34.42.194.164:8189'

const iframeLoading = ref(true)
const loadingProgress = ref(0)
let progressTimer = null

function startProgress() {
  loadingProgress.value = 0
  clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    const remaining = 99 - loadingProgress.value
    if (remaining > 0) {
      // 变慢趋势，会卡在 99% 等待内部引擎
      loadingProgress.value += remaining * 0.05 + 0.2
    }
  }, 250)
}

function onIframeLoad() {
  // HTML 框架加载完毕。ComfyUI 内部需经过较长 JS 初始化与网络请求才会画出自身 UI。
  // 额外驻留 2800ms，以完美掩盖内部初始化的大段白屏，实现自定义进度条直接到成品界面的无缝衔接。
  setTimeout(() => {
    clearInterval(progressTimer)
    loadingProgress.value = 100
    setTimeout(() => {
      iframeLoading.value = false
    }, 450)
  }, 2800)
}

onMounted(() => {
  startProgress()
})

onBeforeUnmount(() => {
  clearInterval(progressTimer)
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--surface-secondary);
}

.dashboard-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  /* 不用 overflow:hidden，避免裁剪 iframe 导致浏览器节流 */
  overflow: visible;
  width: 100%;
  transition: margin-left var(--sidebar-transition);
}

.content-stack {
  flex: 1;
  position: relative;
  min-height: 0;
  /* 不裁剪，让 iframe 始终在可视区域内 */
  overflow: visible;
}

/* ── ComfyUI 面板 ── */
.comfyui-pane {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  /* opacity:0 隐藏但保持渲染；pointer-events:none 屏蔽交互 */
  opacity: 1;
  pointer-events: auto;
  transition: opacity 0.2s ease;
}

.comfyui-pane--hidden {
  opacity: 0;
  pointer-events: none;
}

/* ── 进度遮罩恢复 ── */
.comfyui-loading {
  position: absolute;
  inset: 0;
  z-index: 5;
  background: #111827;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.loading-track {
  width: 280px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.loading-fill {
  height: 100%;
  background: linear-gradient(90deg, #f97316, #8b5cf6);
  border-radius: 4px;
  transition: width 0.25s ease;
}

.loading-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.02em;
}

.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-leave-to {
  opacity: 0;
}

.comfyui-frame {
  width: 100%;
  flex: 1;
  border: none;
  display: block;
  min-height: 0;
}

/* ── 普通页面 ── */
.dashboard-content {
  position: absolute;
  inset: 0;
  padding: var(--space-6);
  overflow-y: auto;
  background: var(--surface-secondary);
  /* 正常时在 iframe 上方（z-index 更高） */
  z-index: 1;
  transition: opacity 0.2s ease, visibility 0.2s ease;
}

/*
  ComfyUI 路由激活时，通过透明度和可见性隐藏普通页面，
  避免产生由于强制外移带来的潜在水平滚动条（overflow 隐患），同时不会遮盖后面运行的 iframe。
*/
.dashboard-content--offscreen {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

.page-wrapper {
  min-height: 100%;
  width: 100%;
  position: relative;
}

/* ── Page fade transition ── */
.page-fade-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  position: absolute;
  inset: 0;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: var(--space-4);
  }
}
</style>
