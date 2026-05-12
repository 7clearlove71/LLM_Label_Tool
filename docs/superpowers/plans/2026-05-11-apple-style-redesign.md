# Apple 风格前端重设计 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 LLM 训练数据查看器前端从 Element Plus 默认样式改造为 Apple 设计规范风格，功能逻辑不变。

**Architecture:** 保留 Element Plus 组件库，通过全局 CSS 变量覆盖 + scoped 样式深度定制外观。从底层（全局 token + style.css）开始，逐层向上改造各组件。新增侧边栏拖拽调整宽度功能。

**Tech Stack:** Vue 3, Element Plus (CSS override), 原生 CSS 变量

**Spec:** `docs/superpowers/specs/2026-05-11-apple-style-redesign.md`

**验证方式：** 每个任务完成后运行 `cd frontend && npm run build` 确认无编译错误，然后启动 dev server 视觉验证。

---

### Task 1: 全局 CSS Token + Element Plus 覆盖

**Files:**
- Rewrite: `frontend/src/style.css`

- [ ] **Step 1: 重写 style.css**

清除 Vite 默认模板样式，替换为 Apple design token 定义和 Element Plus 全局覆盖：

```css
:root {
  /* === Apple Design Tokens === */

  /* Colors */
  --apple-primary: #0066cc;
  --apple-primary-focus: #0071e3;
  --apple-primary-on-dark: #2997ff;
  --apple-ink: #1d1d1f;
  --apple-ink-muted-80: #333333;
  --apple-ink-muted-48: #7a7a7a;
  --apple-canvas: #ffffff;
  --apple-canvas-parchment: #f5f5f7;
  --apple-surface-pearl: #fafafc;
  --apple-surface-black: #000000;
  --apple-on-dark: #ffffff;
  --apple-divider-soft: #f0f0f0;
  --apple-hairline: #e0e0e0;

  /* Rounded */
  --rounded-sm: 8px;
  --rounded-md: 11px;
  --rounded-lg: 18px;
  --rounded-pill: 9999px;

  /* Spacing */
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 17px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Typography */
  --font-family: system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif;
  --font-mono: 'SF Mono', ui-monospace, Consolas, monospace;

  /* Element Plus Overrides */
  --el-color-primary: #0066cc;
  --el-color-primary-light-3: #3385d6;
  --el-color-primary-light-5: #66a3e0;
  --el-color-primary-light-7: #99c2eb;
  --el-color-primary-light-8: #b3d1f0;
  --el-color-primary-light-9: #cce0f5;
  --el-color-primary-dark-2: #0052a3;
  --el-border-radius-base: 8px;
  --el-font-size-base: 14px;
  --el-font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --el-border-color: #e0e0e0;
  --el-border-color-light: #f0f0f0;
  --el-border-color-lighter: #f5f5f7;
  --el-fill-color-light: #f5f5f7;
  --el-text-color-primary: #1d1d1f;
  --el-text-color-regular: #333333;
  --el-text-color-secondary: #7a7a7a;
  --el-text-color-placeholder: #7a7a7a;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  color: var(--apple-ink);
  background: var(--apple-canvas);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功无错误

- [ ] **Step 3: 提交**

```bash
git add frontend/src/style.css
git commit -m "style: 全局 Apple design token 和 Element Plus CSS 变量覆盖"
```

---

### Task 2: App.vue — 导航栏 + 布局 + 侧边栏拖拽

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 重写 App.vue 的 template**

将 header 改为黑色导航栏，新增拖拽手柄 div，并支持"另存为"按钮上移到导航栏。新增 `save-as` 事件从 DataView 透传上来：

```html
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
          @save-as="showSaveAsDialog = true"
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
```

- [ ] **Step 2: 重写 App.vue 的 script**

```html
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
```

- [ ] **Step 3: 重写 App.vue 的 style**

```html
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family);
  background: var(--apple-canvas);
  color: var(--apple-ink);
}

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
```

- [ ] **Step 4: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功无错误

- [ ] **Step 5: 提交**

```bash
git add frontend/src/App.vue
git commit -m "style: App.vue 黑色导航栏 + 侧边栏拖拽 + Apple 布局"
```

---

### Task 3: PathInput.vue — Pill 输入框 + 书签标签

**Files:**
- Modify: `frontend/src/components/PathInput.vue`

- [ ] **Step 1: 重写 PathInput.vue 的 template**

将 el-input 的 append 按钮改为独立 pill 按钮，书签标签改为自定义 pill 样式：

```html
<template>
  <div class="path-input">
    <div class="input-row">
      <el-input
        v-model="path"
        placeholder="输入文件夹路径，如 /data/training"
        @keyup.enter="handleScan"
        size="default"
        class="path-field"
      >
        <template #suffix>
          <button
            class="star-btn"
            @click="addBookmark"
            :disabled="!path.trim()"
            title="收藏当前路径"
          >
            ★
          </button>
        </template>
      </el-input>
    </div>
    <button class="scan-btn" @click="handleScan" :disabled="loading">
      {{ loading ? '扫描中...' : '扫描' }}
    </button>
    <div class="bookmark-tags" v-if="bookmarkData.bookmarks.length">
      <span
        v-for="bm in bookmarkData.bookmarks"
        :key="bm"
        class="bookmark-pill"
        :class="{ active: bm === bookmarkData.default }"
        @click="onTagClick(bm)"
        @contextmenu.prevent="setDefault(bm)"
      >
        <el-tooltip :content="bm" placement="top" :show-after="500">
          <span class="pill-label">{{ shortName(bm) }}</span>
        </el-tooltip>
        <span class="pill-close" @click.stop="removeBookmark(bm)">×</span>
      </span>
    </div>
  </div>
</template>
```

- [ ] **Step 2: script 不变**

`<script setup>` 部分完全保持原样不动。

- [ ] **Step 3: 重写 style**

```html
<style scoped>
.path-input {
  padding: 16px;
  border-bottom: 1px solid var(--apple-hairline);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input-row {
  width: 100%;
}

.path-field :deep(.el-input__wrapper) {
  border-radius: var(--rounded-pill);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
  padding: 0 16px;
  height: 36px;
}

.path-field :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px var(--apple-primary-focus);
}

.path-field :deep(.el-input__inner) {
  font-size: 14px;
  letter-spacing: -0.224px;
}

.star-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: #e6a23c;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.star-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.scan-btn {
  width: 100%;
  height: 36px;
  border: none;
  border-radius: var(--rounded-pill);
  background: var(--apple-primary);
  color: var(--apple-on-dark);
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  cursor: pointer;
  transition: background 0.15s;
}

.scan-btn:hover {
  background: var(--apple-primary-focus);
}

.scan-btn:active {
  transform: scale(0.95);
}

.scan-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.bookmark-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bookmark-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: var(--rounded-pill);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: -0.12px;
  cursor: pointer;
  background: var(--apple-canvas);
  color: var(--apple-ink-muted-80);
  border: 1px solid var(--apple-hairline);
  transition: background 0.15s;
  max-width: 140px;
}

.bookmark-pill.active {
  background: var(--apple-primary);
  color: var(--apple-on-dark);
  border-color: var(--apple-primary);
}

.bookmark-pill:active {
  transform: scale(0.95);
}

.pill-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 90px;
}

.pill-close {
  font-size: 14px;
  line-height: 1;
  opacity: 0.6;
}

.pill-close:hover {
  opacity: 1;
}

.bookmark-pill.active .pill-close {
  color: var(--apple-on-dark);
}
</style>
```

- [ ] **Step 4: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/PathInput.vue
git commit -m "style: PathInput pill 输入框 + 自定义书签标签"
```

---

### Task 4: FileTree.vue — Apple 风格文件树

**Files:**
- Modify: `frontend/src/components/FileTree.vue`

- [ ] **Step 1: 重写 style 部分**

template 和 script 不动，仅改 style：

```html
<style scoped>
.file-tree {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xs);
}

.file-tree :deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: rgba(0, 0, 0, 0.04);
}

.file-tree :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: var(--rounded-sm);
  padding-left: 8px !important;
}

.file-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(0, 102, 204, 0.08);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: var(--apple-ink);
  width: 100%;
}

.node-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-size {
  color: var(--apple-ink-muted-48);
  font-size: 12px;
  letter-spacing: -0.12px;
  flex-shrink: 0;
}

.empty-tip {
  padding: var(--space-lg);
  text-align: center;
  color: var(--apple-ink-muted-48);
  font-size: 14px;
  letter-spacing: -0.224px;
}
</style>
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/FileTree.vue
git commit -m "style: FileTree Apple 风格选中高亮和字体"
```

---

### Task 5: Toolbar.vue — Pill 搜索栏

**Files:**
- Modify: `frontend/src/components/Toolbar.vue`

- [ ] **Step 1: 重写 Toolbar.vue template**

移除"另存为"按钮（已上移到导航栏），搜索按钮改为自定义 pill：

```html
<template>
  <div class="toolbar">
    <el-input
      v-model="keyword"
      placeholder="搜索内容..."
      clearable
      size="default"
      class="search-input"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <el-select
      v-model="selectedField"
      placeholder="全部字段"
      clearable
      size="default"
      class="field-select"
    >
      <el-option
        v-for="field in fields"
        :key="field.name"
        :label="field.name"
        :value="field.name"
      />
    </el-select>
    <button class="search-btn" @click="handleSearch">搜索</button>
  </div>
</template>
```

- [ ] **Step 2: 移除 emit 中的 save-as**

script 里移除 `'save-as'` 相关的 emit 声明（不再需要）：

```html
<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['search'])
const keyword = ref('')
const selectedField = ref('')

function handleSearch() {
  emit('search', { keyword: keyword.value, field: selectedField.value || null })
}
</script>
```

- [ ] **Step 3: 重写 style**

```html
<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  border-bottom: 1px solid var(--apple-divider-soft);
}

.search-input {
  width: 280px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: var(--rounded-pill);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
  height: 36px;
  padding: 0 16px;
}

.search-input :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px var(--apple-primary-focus);
}

.search-input :deep(.el-input__inner) {
  font-size: 14px;
  letter-spacing: -0.224px;
}

.search-input :deep(.el-input__prefix .el-icon) {
  color: var(--apple-ink-muted-48);
}

.field-select {
  width: 150px;
}

.field-select :deep(.el-input__wrapper) {
  border-radius: var(--rounded-md);
  background: var(--apple-surface-pearl);
  box-shadow: 0 0 0 1px var(--apple-divider-soft);
  height: 36px;
}

.field-select :deep(.el-input__inner) {
  font-size: 14px;
  letter-spacing: -0.224px;
}

.search-btn {
  height: 36px;
  padding: 0 20px;
  border: none;
  border-radius: var(--rounded-pill);
  background: var(--apple-primary);
  color: var(--apple-on-dark);
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}

.search-btn:hover {
  background: var(--apple-primary-focus);
}

.search-btn:active {
  transform: scale(0.95);
}
</style>
```

- [ ] **Step 4: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/Toolbar.vue
git commit -m "style: Toolbar pill 搜索栏 + Pearl 字段选择器"
```

---

### Task 6: DataView.vue — 移除另存为按钮、调整空状态

**Files:**
- Modify: `frontend/src/components/DataView.vue`

- [ ] **Step 1: 重写 DataView.vue**

移除 Toolbar 上的 `@save-as` 和底部的另存为 dialog（已上移到 App.vue），移除 `showSaveAsDialog`/`saveAsPath`/`handleSaveAs` 相关逻辑，空状态改用 Apple 字体样式：

```html
<template>
  <div class="data-view" v-if="filePath">
    <Toolbar
      :fields="schema.fields"
      @search="handleSearch"
    />
    <DataTable
      :rows="rows"
      :schema="schema"
      :offset="offset"
      @row-click="handleRowClick"
    />
    <PaginationBar
      :total="total"
      :page-size="pageSize"
      :all-loaded="allLoaded"
      @page-change="handlePageChange"
      @load-all="handleLoadAll"
    />
    <DetailDrawer
      v-model:visible="drawerVisible"
      :row="selectedRow"
      :row-index="selectedRowIndex"
      :schema="schema"
      :file-path="filePath"
      @saved="reloadCurrentPage"
      @deleted="reloadCurrentPage"
    />
  </div>
  <div v-else class="empty-state">
    <p>请在左侧选择一个文件</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Toolbar from './Toolbar.vue'
import DataTable from './DataTable.vue'
import PaginationBar from './PaginationBar.vue'
import DetailDrawer from './DetailDrawer.vue'
import { readFile, readFileAll, searchFile } from '../api'

const props = defineProps({
  filePath: { type: String, default: '' },
})

const rows = ref([])
const schema = ref({ fields: [] })
const total = ref(0)
const offset = ref(0)
const pageSize = 10
const allLoaded = ref(false)

const drawerVisible = ref(false)
const selectedRow = ref(null)
const selectedRowIndex = ref(0)

async function loadData(newOffset = 0) {
  if (!props.filePath) return
  const { data } = await readFile(props.filePath, newOffset, pageSize)
  rows.value = data.rows
  total.value = data.total
  schema.value = data.schema
  offset.value = newOffset
  allLoaded.value = false
}

async function handleLoadAll() {
  const { data } = await readFileAll(props.filePath)
  rows.value = data.rows
  total.value = data.total
  schema.value = data.schema
  offset.value = 0
  allLoaded.value = true
}

async function handlePageChange(newOffset) {
  await loadData(newOffset)
}

async function handleSearch({ keyword, field }) {
  if (!keyword) {
    await loadData(0)
    return
  }
  const { data } = await searchFile(props.filePath, keyword, field)
  rows.value = data.results.map((r) => r.data)
  total.value = data.count
  offset.value = 0
  allLoaded.value = true
}

function handleRowClick({ row, index }) {
  selectedRow.value = row
  selectedRowIndex.value = index
  drawerVisible.value = true
}

async function reloadCurrentPage() {
  await loadData(offset.value)
}

watch(() => props.filePath, () => {
  if (props.filePath) loadData(0)
}, { immediate: true })
</script>

<style scoped>
.data-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--apple-ink-muted-48);
  font-size: 17px;
  font-weight: 400;
  letter-spacing: -0.374px;
}
</style>
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/DataView.vue
git commit -m "refactor: DataView 移除另存为（已上移到导航栏），Apple 空状态样式"
```

---

### Task 7: DataTable.vue — Apple 数据卡片

**Files:**
- Modify: `frontend/src/components/DataTable.vue`

- [ ] **Step 1: template 和 script 不变，重写 style**

```html
<style scoped>
.data-card-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.data-card {
  border: 1px solid var(--apple-hairline);
  border-radius: var(--rounded-lg);
  padding: 20px var(--space-lg);
  cursor: pointer;
  transition: border-color 0.15s;
  background: var(--apple-canvas);
}

.data-card:hover {
  border-color: var(--apple-primary);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.card-index {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.224px;
  color: var(--apple-primary);
}

.card-expand-hint {
  font-size: 12px;
  letter-spacing: -0.12px;
  color: var(--apple-ink-muted-48);
}

.card-fields {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: 10px;
}

.card-field-tag {
  font-size: 12px;
  letter-spacing: -0.12px;
  color: var(--apple-ink-muted-80);
  background: var(--apple-canvas-parchment);
  padding: 2px var(--space-xs);
  border-radius: var(--space-xxs);
}

.field-name {
  font-weight: 600;
  color: var(--apple-ink-muted-48);
  margin-right: 4px;
}

/* 对话预览 */
.mini-conversation {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mini-msg {
  padding: 10px 14px;
  border-radius: var(--rounded-sm);
  font-size: 14px;
  line-height: 1.47;
  letter-spacing: -0.224px;
}

.mini-role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-right: var(--space-xs);
  letter-spacing: 0;
}

.mini-content {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}

.role-system { background: var(--apple-canvas-parchment); }
.role-system .mini-role { color: var(--apple-ink-muted-48); }

.role-user { background: #f0f9eb; }
.role-user .mini-role { color: #67c23a; }

.role-assistant { background: #f0f4ff; }
.role-assistant .mini-role { color: var(--apple-primary); }

.mini-more {
  font-size: 12px;
  color: var(--apple-ink-muted-48);
  text-align: center;
  padding: var(--space-xxs);
}

/* 偏好预览 */
.pref-preview {
  display: flex;
  gap: var(--space-sm);
}

.pref-side {
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--rounded-sm);
  font-size: 14px;
  line-height: 1.47;
}

.pref-side.chosen {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.pref-side.rejected {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.pref-label {
  font-size: 11px;
  font-weight: 600;
  display: block;
  margin-bottom: var(--space-xxs);
}

.pref-text {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}

/* 指令预览 */
.instruction-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.inst-section {
  background: var(--apple-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: 10px 14px;
}

.inst-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--apple-ink-muted-48);
  text-transform: uppercase;
  display: block;
  margin-bottom: var(--space-xxs);
}

.inst-text {
  font-size: 14px;
  line-height: 1.47;
  letter-spacing: -0.224px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}

/* 通用字段 */
.generic-fields {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.generic-field {
  font-size: 14px;
  line-height: 1.47;
  letter-spacing: -0.224px;
}

.field-value {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}

.no-data {
  text-align: center;
  color: var(--apple-ink-muted-48);
  padding: 48px;
  font-size: 14px;
}
</style>
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/DataTable.vue
git commit -m "style: DataTable Apple 风格卡片 — 18px 圆角, hairline 边框, 蓝色 hover"
```

---

### Task 8: PaginationBar.vue — Apple 分页样式

**Files:**
- Modify: `frontend/src/components/PaginationBar.vue`

- [ ] **Step 1: template 和 script 不变，重写 style**

```html
<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: var(--space-sm) var(--space-lg);
  border-top: 1px solid var(--apple-divider-soft);
}

.total-info {
  color: var(--apple-ink-muted-48);
  font-size: 14px;
  letter-spacing: -0.224px;
}

.pagination-bar :deep(.el-pagination) {
  --el-pagination-button-width: 32px;
  --el-pagination-button-height: 32px;
  --el-pagination-font-size: 13px;
}

.pagination-bar :deep(.el-pager li) {
  border-radius: var(--rounded-sm);
  background: var(--apple-surface-pearl);
  color: var(--apple-ink);
  font-weight: 400;
  min-width: 32px;
}

.pagination-bar :deep(.el-pager li.is-active) {
  background: var(--apple-primary);
  color: var(--apple-on-dark);
}

.pagination-bar :deep(.btn-prev),
.pagination-bar :deep(.btn-next) {
  border-radius: var(--rounded-sm);
  background: var(--apple-surface-pearl);
  color: var(--apple-ink-muted-48);
}

.all-loaded-tip {
  color: var(--apple-ink-muted-48);
  font-size: 12px;
  letter-spacing: -0.12px;
}

.pagination-bar :deep(.el-button--primary.is-link) {
  color: var(--apple-primary);
  font-size: 14px;
}
</style>
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/PaginationBar.vue
git commit -m "style: PaginationBar Apple 分页样式 — 圆角页码, 蓝色激活态"
```

---

### Task 9: DetailDrawer.vue — Apple 抽屉 + Tabs

**Files:**
- Modify: `frontend/src/components/DetailDrawer.vue`

- [ ] **Step 1: 在 DetailDrawer.vue 底部新增 style 块**

template 和 script 不动，新增 scoped style：

```html
<style scoped>
:deep(.el-drawer) {
  border-left: 1px solid var(--apple-hairline);
  box-shadow: none !important;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 24px 16px;
}

:deep(.el-drawer__header span) {
  font-size: 21px;
  font-weight: 600;
  line-height: 1.19;
  letter-spacing: 0.231px;
  color: var(--apple-ink);
}

:deep(.el-drawer__body) {
  padding: 0 24px 24px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--apple-divider-soft);
}

:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: var(--apple-ink-muted-48);
}

:deep(.el-tabs__item.is-active) {
  font-weight: 600;
  color: var(--apple-ink);
}

:deep(.el-tabs__active-bar) {
  background-color: var(--apple-primary);
  height: 2px;
}
</style>
```

- [ ] **Step 2: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/DetailDrawer.vue
git commit -m "style: DetailDrawer Apple 抽屉 + tabs 蓝色激活下划线"
```

---

### Task 10: 渲染组件 — ConversationView + PreferenceView + InstructionView + EditorView + JsonTreeView

**Files:**
- Modify: `frontend/src/renderers/ConversationView.vue`
- Modify: `frontend/src/renderers/PreferenceView.vue`
- Modify: `frontend/src/renderers/InstructionView.vue`
- Modify: `frontend/src/renderers/EditorView.vue`
- Modify: `frontend/src/renderers/JsonTreeView.vue`

- [ ] **Step 1: 重写 ConversationView.vue style**

```html
<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.message-bubble {
  border-radius: var(--rounded-sm);
  padding: 14px 18px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0;
}

.role-system {
  background: var(--apple-canvas-parchment);
}
.role-system .role-label { color: var(--apple-ink-muted-48); }

.role-user {
  background: #f0f9eb;
}
.role-user .role-label { color: #67c23a; }

.role-assistant {
  background: #f0f4ff;
}
.role-assistant .role-label { color: var(--apple-primary); }

.content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
```

- [ ] **Step 2: 重写 PreferenceView.vue style**

```html
<style scoped>
.preference-view {
  display: flex;
  gap: 16px;
}

.pref-column {
  flex: 1;
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.chosen {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.rejected {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.pref-label {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.224px;
  margin-bottom: var(--space-xs);
}

.pref-content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
```

- [ ] **Step 3: 重写 InstructionView.vue style**

```html
<style scoped>
.instruction-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section {
  background: var(--apple-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-ink-muted-48);
  text-transform: uppercase;
  margin-bottom: var(--space-xs);
  letter-spacing: -0.12px;
}

.section-content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
```

- [ ] **Step 4: 重写 EditorView.vue style**

```html
<style scoped>
.editor-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.json-editor :deep(.el-textarea__inner) {
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.5;
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.error-tip {
  color: #f56c6c;
  font-size: 12px;
  letter-spacing: -0.12px;
}

.editor-actions {
  display: flex;
  gap: var(--space-xs);
}

.editor-actions :deep(.el-button--primary) {
  border-radius: var(--rounded-pill);
  padding: 10px 22px;
}

.editor-actions :deep(.el-button--default) {
  border-radius: var(--rounded-pill);
  padding: 10px 22px;
  color: var(--apple-primary);
  border-color: var(--apple-primary);
}

.editor-actions :deep(.el-button:active) {
  transform: scale(0.95);
}
</style>
```

- [ ] **Step 5: 重写 JsonTreeView.vue style**

```html
<style scoped>
.json-tree-view {
  padding: var(--space-xs);
  font-size: 14px;
  letter-spacing: -0.224px;
}
</style>
```

- [ ] **Step 6: 验证构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功

- [ ] **Step 7: 提交**

```bash
git add frontend/src/renderers/
git commit -m "style: 渲染组件 Apple 字体和颜色 — Conversation, Preference, Instruction, Editor, JsonTree"
```

---

### Task 11: 最终验证 — 构建 + 视觉检查

**Files:** 无新修改

- [ ] **Step 1: 生产构建**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build`
Expected: 构建成功，无 warning

- [ ] **Step 2: 启动 dev server 视觉检查**

Run: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool && python main.py --port 8000`

打开 http://localhost:8000，检查以下内容：
1. 顶部黑色导航栏显示标题和"另存为"按钮
2. 侧边栏 parchment 背景，pill 输入框，pill 书签标签，扫描按钮
3. 侧边栏拖拽手柄可用，hover 变蓝，拖拽顺滑
4. 文件树选中高亮为浅蓝底
5. 工具栏 pill 搜索框 + Pearl 选择器 + pill 搜索按钮
6. 数据卡片 18px 圆角，hover 蓝色边框
7. 分页栏圆角页码按钮
8. 详情抽屉标题 21px，tabs 蓝色下划线
9. 对话/偏好/指令渲染组件字体和颜色正确
10. 编辑器 pill 按钮样式

- [ ] **Step 3: 修复任何视觉问题并提交**
