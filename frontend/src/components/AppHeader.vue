<template>
  <header class="app-header">
    <div class="header-left">
      <button class="hamburger-btn" @click="$emit('toggle-sidebar')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <nav class="breadcrumb">
        <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
          <span v-if="idx > 0" class="breadcrumb-sep">/</span>
          <router-link
            v-if="crumb.path"
            :to="crumb.path"
            class="breadcrumb-link"
          >{{ crumb.label }}</router-link>
          <span v-else class="breadcrumb-current">{{ crumb.label }}</span>
        </template>
      </nav>
    </div>

    <div class="header-right">
      <div class="user-info">
        <div class="user-avatar">{{ avatarLetter }}</div>
        <span class="user-name">{{ username }}</span>
      </div>
      <button class="logout-btn" @click="handleLogout">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()

const username = localStorage.getItem('task_manager_username') || 'Admin'
const avatarLetter = computed(() => (username[0] || 'A').toUpperCase())

const menuLabels = {
  tasks: '任务列表',
  templates: '工作流模板',
  settings: '设置'
}

const breadcrumbs = computed(() => {
  const crumbs = []
  const parent = route.meta?.parent
  if (parent && menuLabels[parent]) {
    crumbs.push({
      label: menuLabels[parent],
      path: parent === 'tasks' ? '/dashboard' : `/dashboard/${parent}`
    })
  }
  const title = route.meta?.title
  if (title) {
    crumbs.push({ label: title, path: '' })
  }
  return crumbs
})

function handleLogout() {
  localStorage.removeItem('task_manager_token')
  localStorage.removeItem('task_manager_username')
  router.replace('/login')
}
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.hamburger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) ease;
}

.hamburger-btn:hover {
  background: var(--surface-tertiary);
  color: var(--text-primary);
}

/* ── Breadcrumb ── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
}

.breadcrumb-sep {
  color: var(--text-tertiary);
  font-size: 12px;
}

.breadcrumb-link {
  color: var(--text-tertiary);
  text-decoration: none;
  transition: color var(--duration-fast) ease;
}

.breadcrumb-link:hover {
  color: var(--brand);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 600;
}

/* ── Right side ── */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--brand) 0%, var(--accent) 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-fast) ease;
}

.logout-btn:hover {
  background: var(--danger-soft);
  color: var(--danger);
}
</style>
