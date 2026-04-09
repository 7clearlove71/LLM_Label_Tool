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
