<template>
  <router-view v-slot="{ Component, route }">
    <component :is="Component" :key="route.path" class="route-view" />
  </router-view>
</template>

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
