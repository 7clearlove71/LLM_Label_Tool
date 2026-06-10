<template>
  <div class="request-module">
    <aside class="rm-sidebar">
      <SampleList
        :samples="store.samples" :active-id="activeId"
        @load="loadSample" @delete="deleteSample" @rename="renameSample"
      />
    </aside>
    <main class="rm-main">
      <RequestBuilder
        :spec="spec" :loading="sending" :can-update="!!activeId"
        @update:spec="onSpecChange"
        @send="send"
        @import-curl="showImport = true"
        @copy-curl="copyCurl"
        @save-as="saveAsSample"
        @update-sample="updateSample"
      />
      <ResponseView :response="response" :loading="sending" />
    </main>

    <CurlImportDialog v-model="showImport" @imported="onCurlImported" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SampleList from '../components/request/SampleList.vue'
import RequestBuilder from '../components/request/RequestBuilder.vue'
import ResponseView from '../components/request/ResponseView.vue'
import CurlImportDialog from '../components/request/CurlImportDialog.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples } from '../api'

function emptySpec() {
  return { method: 'GET', url: '', params: [], headers: [], body_type: 'none', body: '', form_body: [] }
}

// 深拷贝快照：样例保存的请求与正在编辑的 spec 解耦
function snapshot(s) {
  return JSON.parse(JSON.stringify(s))
}

const store = ref({ samples: [], draft: null })
const spec = ref(emptySpec())
const activeId = ref('')
const response = ref(null)
const sending = ref(false)
const showImport = ref(false)

let saveTimer = null

// 串行化所有 persist：避免并发 PUT 因网络重排互相覆盖。
// 每个排队任务在执行时读取最新的 store/spec，发送完整状态。
let persistChain = Promise.resolve()
function persist() {
  const run = () => saveRequestSamples({ samples: store.value.samples, draft: spec.value })
  const result = persistChain.then(run, run)
  persistChain = result.catch(() => {})
  return result
}

onMounted(async () => {
  try {
    const { data } = await getRequestSamples()
    store.value = { samples: data.samples || [], draft: data.draft || null }
    if (store.value.draft) spec.value = { ...emptySpec(), ...store.value.draft }
  } catch (e) {
    ElMessage.error('加载样例失败：' + e.message)
  }
})

function scheduleDraftSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => persist().catch(() => {}), 500)
}

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer)
})

function onSpecChange(next) {
  spec.value = next
  scheduleDraftSave()
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

function onCurlImported(parsed) {
  spec.value = { ...emptySpec(), ...parsed }
  activeId.value = ''
  scheduleDraftSave()
  ElMessage.success('已导入 curl')
}

function loadSample(s) {
  activeId.value = s.id
  spec.value = { ...emptySpec(), ...snapshot(s.request) }
  scheduleDraftSave()
}

async function saveAsSample() {
  let value
  try {
    const res = await ElMessageBox.prompt('样例名称', '另存为样例')
    value = res.value
  } catch (e) {
    return // 用户取消
  }
  if (!value || !value.trim()) return
  const id = String(Date.now())
  const entry = { id, name: value.trim(), request: snapshot(spec.value) }
  store.value.samples.push(entry)
  activeId.value = id
  try {
    await persist()
    ElMessage.success('已保存样例')
  } catch (e) {
    // 回滚乐观写入
    store.value.samples = store.value.samples.filter((s) => s.id !== id)
    if (activeId.value === id) activeId.value = ''
    ElMessage.error('保存样例失败：' + (e.response?.data?.detail || e.message))
  }
}

async function updateSample() {
  const target = store.value.samples.find((s) => s.id === activeId.value)
  if (!target) return
  const prev = target.request
  target.request = snapshot(spec.value)
  try {
    await persist()
    ElMessage.success('已更新样例')
  } catch (e) {
    target.request = prev // 回滚
    ElMessage.error('更新样例失败：' + (e.response?.data?.detail || e.message))
  }
}

async function renameSample({ id, name }) {
  const target = store.value.samples.find((s) => s.id === id)
  if (!target) return
  const prev = target.name
  target.name = name
  try {
    await persist()
  } catch (e) {
    target.name = prev // 回滚
    ElMessage.error('重命名失败：' + (e.response?.data?.detail || e.message))
  }
}

async function deleteSample(id) {
  const prevSamples = store.value.samples
  const prevActive = activeId.value
  store.value.samples = store.value.samples.filter((s) => s.id !== id)
  if (activeId.value === id) activeId.value = ''
  try {
    await persist()
  } catch (e) {
    store.value.samples = prevSamples // 回滚
    activeId.value = prevActive
    ElMessage.error('删除样例失败：' + (e.response?.data?.detail || e.message))
  }
}
</script>

<style scoped>
.request-module { display: flex; flex: 1; min-height: 0; }
.rm-sidebar { width: 260px; flex-shrink: 0; overflow: auto; border-right: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); }
.rm-main { flex: 1; min-width: 0; overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
</style>
