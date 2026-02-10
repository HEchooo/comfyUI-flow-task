<template>
  <div class="login-page">
    <div class="login-glow" />
    <el-card class="login-card">
      <template #header>
        <div class="title">系统登录</div>
      </template>

      <el-form :model="form" @keyup.enter="submit">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" class="login-btn" @click="submit">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { login } from '../api/auth'

const router = useRouter()
const submitting = ref(false)
const form = reactive({
  username: 'admin',
  password: ''
})

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  submitting.value = true
  try {
    const result = await login({ username: form.username, password: form.password })
    localStorage.setItem('task_manager_token', result.access_token)
    localStorage.setItem('task_manager_username', result.username)
    ElMessage.success('登录成功')
    router.replace('/')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '登录失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.login-glow {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(21, 101, 192, 0.22), transparent 70%);
  transform: translateY(-10px);
}

.login-card {
  width: min(420px, 92vw);
  z-index: 1;
  backdrop-filter: blur(3px);
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: #134074;
}

.login-btn {
  width: 100%;
}
</style>
