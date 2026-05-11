<template>
  <div class="app">
    <header class="global-nav">
      <span class="nav-title">LLM 训练数据查看器</span>
      <div class="nav-actions">
        <button
          v-if="selectedFile"
          class="nav-link-btn"
          @click="showSaveAsDialog = true"
        >
          另存为
        </button>
      </div>
    </header>
    <div class="app-body">
      <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <PathInput @scan="onScan" />
        <FileTree :tree="fileTree" @select="onFileSelect" />
      </aside>
      <div
        class="resize-handle"
        @mousedown="startResize"
      ></div>
      <main class="main-content">
        <DataView
          :file-path="selectedFile"
          :key="selectedFile"
        />
      </main>
    </div>
    <el-dialog v-model="showSaveAsDialog" title="另存为" width="500px">
      <el-input v-model="saveAsPath" placeholder="输入目标文件路径" />
      <template #footer>
        <el-button @click="showSaveAsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAs">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PathInput from './components/PathInput.vue'
import FileTree from './components/FileTree.vue'
import DataView from './components/DataView.vue'
import { scanDirectory, saveAs } from './api'

const fileTree = ref(null)
const selectedFile = ref('')
const sidebarWidth = ref(260)
const showSaveAsDialog = ref(false)
const saveAsPath = ref('')

async function onScan(path) {
  const { data } = await scanDirectory(path)
  fileTree.value = data
}

function onFileSelect(filePath) {
  selectedFile.value = filePath
}

function startResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = sidebarWidth.value

  function onMouseMove(ev) {
    const delta = ev.clientX - startX
    const newWidth = Math.min(480, Math.max(180, startWidth + delta))
    sidebarWidth.value = newWidth
  }

  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

async function handleSaveAs() {
  if (!saveAsPath.value.trim() || !selectedFile.value) return
  await saveAs(selectedFile.value, saveAsPath.value.trim())
  ElMessage.success('另存为成功')
  showSaveAsDialog.value = false
  saveAsPath.value = ''
}
</script>

<style>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.global-nav {
  height: 44px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--apple-surface-black);
  flex-shrink: 0;
}

.nav-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--apple-on-dark);
  letter-spacing: -0.12px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link-btn {
  background: none;
  border: none;
  color: var(--apple-on-dark);
  font-family: var(--font-family);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: -0.12px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--rounded-sm);
  transition: background 0.15s;
}

.nav-link-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-link-btn:active {
  transform: scale(0.95);
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  background: var(--apple-canvas-parchment);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.resize-handle {
  width: 4px;
  cursor: col-resize;
  background: var(--apple-hairline);
  flex-shrink: 0;
  transition: background 0.15s;
}

.resize-handle:hover {
  background: var(--apple-primary);
}

.main-content {
  flex: 1;
  overflow: hidden;
  background: var(--apple-canvas);
}
</style>
