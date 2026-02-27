import { createRouter, createWebHistory } from 'vue-router'

import DashboardLayout from '../layouts/DashboardLayout.vue'
import LandingLayout from '../layouts/LandingLayout.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  /* ── Landing page (public, full screen) ── */
  {
    path: '/',
    component: LandingLayout,
    meta: { public: true },
    children: [
      {
        path: '',
        name: 'landing',
        component: () => import('../views/LandingView.vue'),
        meta: { public: true }
      }
    ]
  },

  /* ── Login (standalone, no layout wrapper) ── */
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true }
  },

  /* ── Dashboard (sidebar + header layout) ── */
  {
    path: '/dashboard',
    component: DashboardLayout,
    children: [
      {
        path: '',
        name: 'tasks',
        component: () => import('../views/TaskListView.vue'),
        meta: { title: '任务列表' }
      },
      {
        path: 'tasks/new',
        name: 'task-create',
        component: () => import('../views/TaskFormView.vue'),
        meta: { title: '创建任务', parent: 'tasks' }
      },
      {
        path: 'tasks/:id/edit',
        name: 'task-edit',
        component: () => import('../views/TaskFormView.vue'),
        meta: { title: '编辑任务', parent: 'tasks' }
      },
      {
        path: 'tasks/:id',
        name: 'task-detail',
        component: () => import('../views/TaskDetailView.vue'),
        meta: { title: '任务详情', parent: 'tasks' }
      },
      {
        path: 'templates',
        name: 'templates',
        component: () => import('../views/TaskTemplateListView.vue'),
        meta: { title: '工作流模板' }
      },
      {
        path: 'templates/new',
        name: 'template-create',
        component: () => import('../views/TaskTemplateFormView.vue'),
        meta: { title: '新建工作流', parent: 'templates' }
      },
      {
        path: 'templates/:id/edit',
        name: 'template-edit',
        component: () => import('../views/TaskTemplateFormView.vue'),
        meta: { title: '编辑工作流', parent: 'templates' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/SettingsView.vue'),
        meta: { title: '设置' }
      }
    ]
  },

  /* ── Backward-compatible redirects ── */
  { path: '/tasks/new', redirect: '/dashboard/tasks/new' },
  { path: '/tasks/:id/edit', redirect: to => `/dashboard/tasks/${to.params.id}/edit` },
  { path: '/tasks/:id', redirect: to => `/dashboard/tasks/${to.params.id}` },
  { path: '/templates', redirect: '/dashboard/templates' },
  { path: '/templates/new', redirect: '/dashboard/templates/new' },
  { path: '/templates/:id/edit', redirect: to => `/dashboard/templates/${to.params.id}/edit` },
  { path: '/settings', redirect: '/dashboard/settings' }
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
    return '/dashboard'
  }
  return true
})

export default router
