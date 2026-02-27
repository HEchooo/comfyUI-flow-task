import { createRouter, createWebHistory } from 'vue-router'

import TaskListView from '../views/TaskListView.vue'
import TaskFormView from '../views/TaskFormView.vue'
import TaskDetailView from '../views/TaskDetailView.vue'
import LoginView from '../views/LoginView.vue'
import TaskTemplateListView from '../views/TaskTemplateListView.vue'
import TaskTemplateFormView from '../views/TaskTemplateFormView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  { path: '/login', component: LoginView, meta: { public: true } },
  { path: '/', component: TaskListView },
  { path: '/tasks/new', component: TaskFormView },
  { path: '/tasks/:id/edit', component: TaskFormView },
  { path: '/tasks/:id', component: TaskDetailView },
  { path: '/templates', component: TaskTemplateListView },
  { path: '/templates/new', component: TaskTemplateFormView },
  { path: '/templates/:id/edit', component: TaskTemplateFormView },
  { path: '/settings', component: SettingsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('task_manager_token')
  const isPublic = Boolean(to.meta?.public)

  if (!token && !isPublic) {
    return '/login'
  }
  if (token && to.path === '/login') {
    return '/'
  }
  return true
})

export default router
