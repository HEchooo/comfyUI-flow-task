<template>
  <div class="dashboard-layout" :class="{ 'sidebar-collapsed': isCollapsed }">
    <AppSidebar :collapsed="isCollapsed" @toggle="toggle" />

    <div class="dashboard-main">
      <AppHeader @toggle-sidebar="toggle" />

      <main class="dashboard-content">
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
</template>

<script setup>
import AppSidebar from '../components/AppSidebar.vue'
import AppHeader from '../components/AppHeader.vue'
import { useSidebar } from '../composables/useSidebar'

const { isCollapsed, toggle } = useSidebar()
</script>

<style scoped>
.dashboard-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--sidebar-transition);
  background: var(--surface-secondary);
}

.dashboard-layout.sidebar-collapsed {
  grid-template-columns: var(--sidebar-collapsed-width) 1fr;
}

.dashboard-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow: hidden;
}

.dashboard-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
  position: relative;
}

/* ── Page wrapper for proper transitions ── */
.page-wrapper {
  min-height: 100%;
  width: 100%;
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
  .dashboard-layout {
    grid-template-columns: 0 1fr;
  }

  .dashboard-content {
    padding: var(--space-4);
  }
}
</style>
