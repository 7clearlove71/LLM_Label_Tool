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

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getBookmarks, saveBookmarks } from '../api'

const emit = defineEmits(['scan'])
const path = ref('')
const loading = ref(false)
const bookmarkData = reactive({ default: null, bookmarks: [] })

onMounted(async () => {
  await fetchBookmarks()
  if (bookmarkData.default) {
    path.value = bookmarkData.default
    handleScan()
  }
})

async function fetchBookmarks() {
  try {
    const { data } = await getBookmarks()
    bookmarkData.default = data.default
    bookmarkData.bookmarks = data.bookmarks
  } catch {
    // 首次使用，无配置文件
  }
}

async function persistBookmarks() {
  await saveBookmarks({ default: bookmarkData.default, bookmarks: bookmarkData.bookmarks })
}

function handleScan() {
  if (!path.value.trim()) return
  loading.value = true
  try {
    emit('scan', path.value.trim())
  } finally {
    loading.value = false
  }
}

async function addBookmark() {
  const p = path.value.trim()
  if (!p) return
  if (bookmarkData.bookmarks.includes(p)) {
    ElMessage.info('该路径已收藏')
    return
  }
  if (bookmarkData.bookmarks.length >= 10) {
    ElMessage.warning('最多保存 10 个地址，请先删除一些')
    return
  }
  bookmarkData.bookmarks.push(p)
  if (!bookmarkData.default) {
    bookmarkData.default = p
  }
  await persistBookmarks()
  ElMessage.success('已收藏')
}

async function removeBookmark(bm) {
  bookmarkData.bookmarks = bookmarkData.bookmarks.filter(b => b !== bm)
  if (bookmarkData.default === bm) {
    bookmarkData.default = bookmarkData.bookmarks[0] || null
  }
  await persistBookmarks()
}

async function setDefault(bm) {
  bookmarkData.default = bm
  await persistBookmarks()
  ElMessage.success('已设为默认')
}

function onTagClick(bm) {
  path.value = bm
  handleScan()
}

function shortName(fullPath) {
  const parts = fullPath.replace(/\/+$/, '').split('/')
  return parts[parts.length - 1] || fullPath
}
</script>

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
