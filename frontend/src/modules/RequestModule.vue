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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SampleList from '../components/request/SampleList.vue'
import RequestBuilder from '../components/request/RequestBuilder.vue'
import ResponseView from '../components/request/ResponseView.vue'
import CurlImportDialog from '../components/request/CurlImportDialog.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples } from '../api'

function emptySpec() {
  return { method: 'GET', url: '', params: [], headers: [], body_type: 'none', body: '', form_body: [] }
}

const store = ref({ samples: [], draft: null })
const spec = ref(emptySpec())
const activeId = ref('')
const response = ref(null)
const sending = ref(false)
const showImport = ref(false)

let saveTimer = null

onMounted(async () => {
  try {
    const { data } = await getRequestSamples()
    store.value = { samples: data.samples || [], draft: data.draft || null }
    if (store.value.draft) spec.value = { ...emptySpec(), ...store.value.draft }
  } catch (e) {
    ElMessage.error('加载样例失败：' + e.message)
  }
})

function persist() {
  return saveRequestSamples({ samples: store.value.samples, draft: spec.value })
}

function scheduleDraftSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => persist().catch(() => {}), 500)
}

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
  spec.value = { ...emptySpec(), ...s.request }
  scheduleDraftSave()
}

async function saveAsSample() {
  try {
    const { value } = await ElMessageBox.prompt('样例名称', '另存为样例')
    if (!value || !value.trim()) return
    const id = String(Date.now())
    store.value.samples.push({ id, name: value.trim(), request: spec.value })
    activeId.value = id
    await persist()
    ElMessage.success('已保存样例')
  } catch (e) { /* 取消 */ }
}

async function updateSample() {
  const target = store.value.samples.find((s) => s.id === activeId.value)
  if (!target) return
  target.request = spec.value
  await persist()
  ElMessage.success('已更新样例')
}

function renameSample({ id, name }) {
  const target = store.value.samples.find((s) => s.id === id)
  if (target) { target.name = name; persist() }
}

async function deleteSample(id) {
  store.value.samples = store.value.samples.filter((s) => s.id !== id)
  if (activeId.value === id) activeId.value = ''
  await persist()
}
</script>

<style scoped>
.request-module { display: flex; flex: 1; min-height: 0; }
.rm-sidebar { width: 260px; flex-shrink: 0; overflow: auto; border-right: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); }
.rm-main { flex: 1; min-width: 0; overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
</style>
