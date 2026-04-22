<template>
  <div class="app">
    <header class="app-header">
      <h1 class="app-title">LLM 训练数据查看器</h1>
    </header>
    <div class="app-body">
      <aside class="sidebar">
        <PathInput @scan="onScan" />
        <FileTree :tree="fileTree" @select="onFileSelect" />
      </aside>
      <main class="main-content">
        <DataView
          :file-path="selectedFile"
          :key="selectedFile"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PathInput from './components/PathInput.vue'
import FileTree from './components/FileTree.vue'
import DataView from './components/DataView.vue'
import { scanDirectory } from './api'

const fileTree = ref(null)
const selectedFile = ref('')

async function onScan(path) {
  const { data } = await scanDirectory(path)
  fileTree.value = data
}

function onFileSelect(filePath) {
  selectedFile.value = filePath
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #ffffff;
  color: #333333;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  height: 56px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
  background: #ffffff;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  border-right: 1px solid #eee;
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: hidden;
  background: #ffffff;
}

/* 禁用 drawer 滑出动画，直接显示 */
.el-drawer__open .el-drawer.rtl,
.el-drawer__open .el-drawer.ltr,
.el-drawer__open .el-drawer.ttb,
.el-drawer__open .el-drawer.btt {
  transition: none !important;
  animation: none !important;
}
.el-overlay {
  transition: none !important;
}
.el-drawer {
  transition: none !important;
}
</style>
