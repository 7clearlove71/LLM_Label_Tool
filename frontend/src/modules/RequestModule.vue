<template>
  <div class="request-module">
    <aside class="rm-sidebar" :style="{ width: sidebarWidth + 'px' }">
      <SampleList
        :samples="store.samples" :active-id="activeId"
        @new="newSample" @import-curl="showImport = true"
        @load="selectSample" @clone="cloneSample" @delete="deleteSample" @rename="renameSample"
      />
    </aside>
    <div class="rm-resize-handle" @mousedown="startResize"></div>
    <main class="rm-main">
      <template v-if="activeId">
        <RequestBuilder
          :spec="spec" :loading="sending" :save-state="saveState"
          @update:spec="onSpecChange"
          @send="send"
          @copy-curl="copyCurl"
        />
        <ResponseView :response="response" :loading="sending" />
      </template>
      <div v-else class="rm-empty">
        <p class="rm-empty-tip">还没有请求样例</p>
        <div class="rm-empty-actions">
          <el-button type="primary" @click="newSample">新建请求</el-button>
          <el-button @click="showImport = true">导入 curl</el-button>
        </div>
      </div>
    </main>

    <CurlImportDialog v-model="showImport" @imported="onCurlImported" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import SampleList from '../components/request/SampleList.vue'
import RequestBuilder from '../components/request/RequestBuilder.vue'
import ResponseView from '../components/request/ResponseView.vue'
import CurlImportDialog from '../components/request/CurlImportDialog.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples } from '../api'

function emptySpec() {
  return { method: 'GET', url: '', params: [], headers: [], body_type: 'none', body: '', form_body: [] }
}
function snapshot(s) {
  return JSON.parse(JSON.stringify(s))
}
function genId() {
  return String(Date.now()) + '-' + Math.random().toString(36).slice(2, 6)
}
function nameFromUrl(url) {
  if (!url) return '导入的请求'
  try {
    const u = new URL(url)
    const name = (u.host + u.pathname).replace(/\/$/, '')
    return name || '导入的请求'
  } catch (e) {
    return '导入的请求'
  }
}
function isDraftMeaningful(d) {
  if (!d) return false
  return !!((d.url && d.url.trim()) || (d.method && d.method !== 'GET') ||
    (d.params && d.params.length) || (d.headers && d.headers.length) ||
    d.body || (d.form_body && d.form_body.length) ||
    (d.body_type && d.body_type !== 'none'))
}

const store = ref({ samples: [] })
const spec = ref(emptySpec())
const activeId = ref('')
const response = ref(null)
const sending = ref(false)
const showImport = ref(false)
const saveState = ref('')
const sidebarWidth = ref(260)

function startResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = sidebarWidth.value
  function onMouseMove(ev) {
    const delta = ev.clientX - startX
    sidebarWidth.value = Math.min(480, Math.max(180, startWidth + delta))
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

let saveTimer = null

// 串行化所有 persist：避免并发 PUT 因网络重排互相覆盖。
let persistChain = Promise.resolve()
function persist() {
  const run = () => saveRequestSamples({ samples: store.value.samples, active_id: activeId.value })
  const result = persistChain.then(run, run)
  persistChain = result.catch(() => {})
  return result
}

onMounted(async () => {
  try {
    const { data } = await getRequestSamples()
    store.value = { samples: data.samples || [] }
    // 旧 draft 一次性迁移为样例
    if (isDraftMeaningful(data.draft)) {
      const entry = { id: genId(), name: '未命名请求', request: { ...emptySpec(), ...data.draft } }
      store.value.samples.push(entry)
      activeId.value = entry.id
      spec.value = { ...emptySpec(), ...snapshot(entry.request) }
      await persist() // 落库迁移结果（不再发送 draft）
      return
    }
    // 恢复上次选中，失败则选第一个
    const restore = data.active_id && store.value.samples.find((s) => s.id === data.active_id)
    const target = restore || store.value.samples[0]
    if (target) {
      activeId.value = target.id
      spec.value = { ...emptySpec(), ...snapshot(target.request) }
    }
  } catch (e) {
    ElMessage.error('加载样例失败：' + e.message)
  }
})

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer)
})

// 编辑当前样例：防抖自动保存，失败仅提示不回滚（避免吞掉输入）
function onSpecChange(next) {
  spec.value = next
  const target = store.value.samples.find((s) => s.id === activeId.value)
  if (!target) return
  target.request = snapshot(next)
  saveState.value = 'saving'
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await persist()
      saveState.value = 'saved'
    } catch (e) {
      saveState.value = ''
      ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
    }
  }, 500)
}

// 结构性新增：乐观写 + 失败回滚
async function addSampleAndSelect(entry) {
  const prevActive = activeId.value
  const prevSpec = spec.value
  store.value.samples.push(entry)
  activeId.value = entry.id
  spec.value = { ...emptySpec(), ...snapshot(entry.request) }
  saveState.value = 'saving'
  try {
    await persist()
    saveState.value = 'saved'
    return true
  } catch (e) {
    store.value.samples = store.value.samples.filter((s) => s.id !== entry.id)
    activeId.value = prevActive
    spec.value = prevSpec
    saveState.value = ''
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
    return false
  }
}

function newSample() {
  return addSampleAndSelect({ id: genId(), name: '未命名请求', request: emptySpec() })
}

function cloneSample(s) {
  return addSampleAndSelect({ id: genId(), name: s.name + ' 副本', request: snapshot(s.request) })
}

async function onCurlImported(parsed) {
  const req = { ...emptySpec(), ...parsed }
  const ok = await addSampleAndSelect({ id: genId(), name: nameFromUrl(req.url), request: req })
  if (ok) ElMessage.success('已导入 curl 并新建样例')
}

function selectSample(s) {
  if (s.id === activeId.value) return
  activeId.value = s.id
  spec.value = { ...emptySpec(), ...snapshot(s.request) }
  // 仅切换选中：静默持久化 active_id（不显示保存指示，纯切换不算编辑）
  persist().catch(() => {})
}

async function renameSample({ id, name }) {
  const target = store.value.samples.find((s) => s.id === id)
  if (!target) return
  const prev = target.name
  target.name = name
  try {
    await persist()
  } catch (e) {
    target.name = prev
    ElMessage.error('重命名失败：' + (e.response?.data?.detail || e.message))
  }
}

async function deleteSample(id) {
  const prevSamples = store.value.samples
  const prevActive = activeId.value
  const prevSpec = spec.value
  store.value.samples = store.value.samples.filter((s) => s.id !== id)
  if (activeId.value === id) {
    const first = store.value.samples[0]
    if (first) {
      activeId.value = first.id
      spec.value = { ...emptySpec(), ...snapshot(first.request) }
    } else {
      activeId.value = ''
      spec.value = emptySpec()
    }
  }
  try {
    await persist()
  } catch (e) {
    store.value.samples = prevSamples
    activeId.value = prevActive
    spec.value = prevSpec
    ElMessage.error('删除样例失败：' + (e.response?.data?.detail || e.message))
  }
}

async function send() {
  sending.value = true
  response.value = null
  try {
    const { data } = await sendRequest(spec.value)
    response.value = data
  } catch (e) {
    response.value = { error: e.response?.data?.detail || e.message }
  } finally {
    sending.value = false
  }
}

async function copyCurl() {
  try {
    const { data } = await toCurl(spec.value)
    await navigator.clipboard.writeText(data.curl)
    ElMessage.success('已复制 curl 到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败：' + e.message)
  }
}
</script>

<style scoped>
.request-module { display: flex; flex: 1; min-height: 0; }
.rm-sidebar { flex-shrink: 0; overflow: auto; }
.rm-resize-handle { width: 4px; cursor: col-resize; background: var(--apple-hairline, rgba(0,0,0,0.08)); flex-shrink: 0; transition: background 0.15s; }
.rm-resize-handle:hover { background: var(--apple-primary, #007aff); }
.rm-main { flex: 1; min-width: 0; overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
.rm-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: #999; }
.rm-empty-tip { font-size: 14px; }
.rm-empty-actions { display: flex; gap: 12px; }
</style>
