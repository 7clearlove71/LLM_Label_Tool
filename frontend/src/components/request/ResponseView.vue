<template>
  <div class="response-view">
    <div v-if="loading" class="resp-placeholder">发送中…</div>
    <div v-else-if="!response" class="resp-placeholder">点「发送」查看响应</div>
    <div v-else-if="response.error" class="resp-error">请求失败：{{ response.error }}</div>
    <template v-else>
      <div class="resp-statusbar">
        <span class="status-code" :class="statusClass">{{ response.status }} {{ response.status_text }}</span>
        <span class="resp-meta">{{ response.elapsed_ms }} ms</span>
        <span class="resp-meta">{{ prettySize }}</span>
        <span v-if="response.truncated" class="resp-meta warn">响应体过大，已截断</span>
      </div>
      <el-tabs v-model="activeTab" class="resp-tabs">
        <el-tab-pane label="Body" name="body">
          <pre class="resp-body">{{ prettyBody }}</pre>
        </el-tab-pane>
        <el-tab-pane label="Headers" name="headers">
          <div v-for="(v, k) in response.headers" :key="k" class="resp-header-row">
            <span class="hk">{{ k }}</span><span class="hv">{{ v }}</span>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  response: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})
const activeTab = ref('body')

watch(
  () => props.response,
  (val) => {
    if (val && !val.error) activeTab.value = 'body'
  }
)

const statusClass = computed(() => {
  const s = props.response?.status || 0
  if (s >= 200 && s < 300) return 'ok'
  if (s >= 400) return 'err'
  return 'other'
})

const prettySize = computed(() => {
  const n = props.response?.size_bytes || 0
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(2) + ' MB'
})

const prettyBody = computed(() => {
  const body = props.response?.body || ''
  const ct = props.response?.content_type || ''
  if (ct.includes('json')) {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch {
      return body
    }
  }
  return body
})
</script>

<style scoped>
.response-view { display: flex; flex-direction: column; min-height: 0; }
.resp-placeholder { padding: 24px; color: #999; }
.resp-error { padding: 16px; color: #ff3b30; }
.resp-statusbar { display: flex; align-items: center; gap: 16px; padding: 10px 4px; font-size: 13px; }
.status-code { font-weight: 600; }
.status-code.ok { color: #34c759; }
.status-code.err { color: #ff3b30; }
.status-code.other { color: #ff9500; }
.resp-meta { color: #888; }
.resp-meta.warn { color: #ff9500; }
.resp-body { margin: 0; padding: 12px; background: #f6f6f8; border-radius: 10px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all; max-height: 50vh; overflow: auto; }
.resp-header-row { display: flex; gap: 12px; padding: 4px 0; font-size: 13px; }
.hk { color: var(--apple-primary, #007aff); min-width: 200px; }
.hv { color: #333; word-break: break-all; }
</style>
