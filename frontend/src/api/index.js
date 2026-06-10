import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 30000,
})

export function scanDirectory(path) {
  return api.post('/api/scan', { path })
}

export function readFile(path, offset = 0, limit = 10) {
  return api.post('/api/file/read', { path, offset, limit })
}

export function readFileAll(path) {
  return api.post('/api/file/read-all', { path })
}

export function updateRow(path, rowIndex, data) {
  return api.post('/api/file/update', { path, row_index: rowIndex, data })
}

export function deleteRow(path, rowIndex) {
  return api.post('/api/file/delete', { path, row_index: rowIndex })
}

export function saveAs(sourcePath, targetPath) {
  return api.post('/api/file/save-as', { source_path: sourcePath, target_path: targetPath })
}

export function searchFile(path, keyword, field = null) {
  return api.post('/api/file/search', { path, keyword, field })
}

export function getBookmarks() {
  return api.get('/api/bookmarks')
}

export function saveBookmarks(data) {
  return api.put('/api/bookmarks', data)
}

export function sendRequest(spec) {
  return api.post('/api/request/send', spec)
}

export function parseCurl(text) {
  return api.post('/api/request/parse-curl', { text })
}

export function toCurl(spec) {
  return api.post('/api/request/to-curl', spec)
}

export function getRequestSamples() {
  return api.get('/api/requests')
}

export function saveRequestSamples(data) {
  return api.put('/api/requests', data)
}

// 解析单个 SSE 块（event: ... / data: ...）
function parseSSEChunk(chunk) {
  let event = 'message'
  let data = ''
  for (const line of chunk.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  if (!data) return null
  try {
    return { event, data: JSON.parse(data) }
  } catch {
    return null
  }
}

// 流式对话：POST spec，逐块回调。onDelta({content,reasoning}) / onError(msg)。
// 返回 Promise，结束（done/流关闭/abort）后 resolve。
export async function chatStream(spec, { onDelta, onError, signal }) {
  let resp
  try {
    resp = await fetch('/api/request/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
      signal,
    })
  } catch (e) {
    if (e.name !== 'AbortError') onError(e.message)
    return
  }
  if (!resp.ok || !resp.body) {
    onError(`HTTP ${resp.status}`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const chunks = buf.split('\n\n')
      buf = chunks.pop()
      for (const chunk of chunks) {
        const ev = parseSSEChunk(chunk)
        if (!ev) continue
        if (ev.event === 'delta') onDelta(ev.data)
        else if (ev.event === 'error') onError(ev.data.message || '上游错误')
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') onError(e.message)
  }
}
