<template>
  <el-container class="app-shell">
    <div class="bg-shape bg-shape-left" />
    <div class="bg-shape bg-shape-right" />

    <el-header class="app-header">
      <button class="brand-wrap brand-link" type="button" @click="goHome">
        <div class="brand-dot" />
        <div class="brand">ComfyUI Task Manager</div>
      </button>
      <div class="header-right">
        <el-button v-if="!isLoginPage" size="small" @click="goSettings">设置</el-button>
        <el-button v-if="!isLoginPage" type="danger" plain size="small" @click="logout">退出登录</el-button>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isLoginPage = computed(() => route.path === '/login')

function logout() {
  localStorage.removeItem('task_manager_token')
  localStorage.removeItem('task_manager_username')
  router.replace('/login')
}

function goHome() {
  router.push('/')
}

function goSettings() {
  router.push('/settings')
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(4px);
  opacity: 0.34;
  z-index: 0;
  animation: drift 12s ease-in-out infinite;
}

.bg-shape-left {
  width: 380px;
  height: 380px;
  top: -120px;
  left: -120px;
  background: radial-gradient(circle, #87b6ff 0%, transparent 70%);
}

.bg-shape-right {
  width: 340px;
  height: 340px;
  right: -120px;
  top: 60px;
  background: radial-gradient(circle, #65d8b7 0%, transparent 70%);
  animation-delay: 1.5s;
}

.app-header {
  z-index: 2;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #d6e7ff;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  padding: 0 20px;
}

.brand-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-link {
  border: 0;
  padding: 0;
  margin: 0;
  background: transparent;
  cursor: pointer;
}

.brand-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1565c0 0%, #1cb992 100%);
  box-shadow: 0 0 0 5px rgba(21, 101, 192, 0.12);
}

.brand {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: #143f7f;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-main {
  z-index: 1;
  position: relative;
  max-width: 1240px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}

@keyframes drift {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(18px);
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 12px;
  }

  .brand {
    font-size: 16px;
  }

  .app-main {
    padding: 12px;
  }
}
</style>
