<template>
  <router-view v-slot="{ Component, route }">
    <component :is="Component" :key="route.path" class="route-view" />
  </router-view>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useIframe, sendRouteChange } from './composables/useIframe'
import { setIframeToken } from './api/http'

const route = useRoute()

// iframe 通信设置
useIframe({
  // 接收父系统传递的 token
  onToken: (token) => {
    console.log('[Iframe] Received token from parent')
    setIframeToken(token)
    // 同时保存到 localStorage，防止页面刷新后丢失
    localStorage.setItem('task_manager_token', token)
  },
  // 响应父系统的导航请求
  onNavigate: (path) => {
    console.log('[Iframe] Parent requested navigation to:', path)
    if (route.path !== path) {
      route.push(path)
    }
  }
})

// 监听路由变化，通知父系统
watch(
  () => route.path,
  (newPath) => {
    sendRouteChange(newPath)
  }
)

onMounted(() => {
  // 检测是否在 iframe 中运行
  if (window.parent !== window) {
    document.body.classList.add('in-iframe')
    console.log('[Iframe] Running in iframe mode')
  }
})
</script>

<style>
/* ── Set body background immediately to prevent white flash ── */
html {
  background: #f8fafc;
}

body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

/* ── iframe 模式下的样式调整 ── */
.in-iframe {
  overflow: hidden;
}

/* ── Each route view is a full-height block ── */
.route-view {
  display: block;
  min-height: 100vh;
  width: 100%;
}

/* ── Landing page background ── */
.route-view:has(.landing-page),
.route-view:has(.landing-layout) {
  background: #0a0e1a;
}

/* ── Dashboard pages background ── */
.route-view:has(.dashboard-layout) {
  background: #f8fafc;
}

/* ── Login page background ── */
.route-view:has(.login-page) {
  background: linear-gradient(180deg, #f4f8ff 0%, #eef4fb 100%);
}
</style>
