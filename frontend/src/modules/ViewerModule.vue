<template>
  <div class="viewer-module">
    <div class="app-body">
      <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <PathInput @scan="onScan" />
        <FileTree :tree="fileTree" @select="onFileSelect" />
      </aside>
      <div class="resize-handle" @mousedown="startResize"></div>
      <main class="main-content">
        <div class="viewer-toolbar" v-if="selectedFile">
          <button class="nav-link-btn" @click="showSaveAsDialog = true">另存为</button>
        </div>
        <DataView :file-path="selectedFile" :key="selectedFile" />
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
import PathInput from '../components/PathInput.vue'
import FileTree from '../components/FileTree.vue'
import DataView from '../components/DataView.vue'
import { scanDirectory, saveAs } from '../api'

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

<style scoped>
.viewer-module {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  display: flex;
  flex-direction: column;
}
.nav-link-btn {
  background: none;
  border: none;
  color: var(--apple-ink-muted-48);
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
  background: var(--apple-canvas-parchment);
}
.nav-link-btn:active {
  transform: scale(0.95);
}
.viewer-toolbar {
  padding: 8px 16px;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
</style>
