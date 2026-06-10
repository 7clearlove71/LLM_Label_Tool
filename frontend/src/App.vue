<template>
  <div class="app">
    <header class="global-nav">
      <span class="nav-title">个人工作空间站</span>
      <nav class="module-tabs">
        <button
          v-for="m in modules"
          :key="m.key"
          class="module-tab"
          :class="{ active: activeModule === m.key }"
          @click="activeModule = m.key"
        >{{ m.label }}</button>
      </nav>
    </header>
    <div class="app-body-shell">
      <ViewerModule v-show="activeModule === 'viewer'" />
      <RequestModule v-show="activeModule === 'request'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ViewerModule from './modules/ViewerModule.vue'
import RequestModule from './modules/RequestModule.vue'

const modules = [
  { key: 'viewer', label: '数据查看器' },
  { key: 'request', label: 'postwoman' }
]
const activeModule = ref('viewer')
</script>

<style>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.global-nav {
  padding: 8px 24px 6px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  background: var(--apple-surface-black);
  flex-shrink: 0;
}

.nav-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--apple-on-dark);
  letter-spacing: -0.2px;
}

.app-body-shell {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.module-tabs {
  display: flex;
  gap: 4px;
}

.module-tab {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.55);
  font-family: var(--font-family);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: -0.12px;
  cursor: pointer;
  padding: 5px 14px;
  border-radius: var(--rounded-sm);
  transition: all 0.15s;
}

.module-tab:hover {
  color: var(--apple-on-dark);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.32);
}

.module-tab.active {
  color: var(--apple-on-dark);
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.45);
  font-weight: 600;
}
</style>
