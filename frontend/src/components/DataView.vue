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
