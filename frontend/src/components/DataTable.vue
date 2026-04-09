<template>
  <div class="data-table-wrapper">
    <el-table
      :data="rows"
      stripe
      highlight-current-row
      @row-click="handleRowClick"
      class="data-table"
      :header-cell-style="{ background: '#f7f8fa', color: '#333', fontWeight: 600 }"
    >
      <el-table-column type="index" label="#" width="60" :index="indexMethod" />
      <el-table-column
        v-for="field in columnFields"
        :key="field.name"
        :prop="field.name"
        :label="field.name"
        :min-width="getColumnWidth(field)"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <span v-if="isSimpleValue(row[field.name])">
            {{ row[field.name] }}
          </span>
          <span v-else class="complex-value">
            {{ summarize(row[field.name]) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  schema: { type: Object, default: () => ({ fields: [] }) },
  offset: { type: Number, default: 0 },
})

const emit = defineEmits(['row-click'])

const columnFields = computed(() => {
  return props.schema.fields || []
})

function indexMethod(index) {
  return props.offset + index + 1
}

function handleRowClick(row, column, event) {
  const rowIndex = props.rows.indexOf(row)
  emit('row-click', { row, index: props.offset + rowIndex })
}

function isSimpleValue(val) {
  return val === null || val === undefined || typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean'
}

function summarize(val) {
  if (Array.isArray(val)) return `[${val.length} items]`
  if (typeof val === 'object' && val !== null) return `{${Object.keys(val).length} keys}`
  return String(val)
}

function getColumnWidth(field) {
  if (field.type === 'number' || field.type === 'boolean') return '100'
  if (field.display === 'detail') return '150'
  return '180'
}
</script>

<style scoped>
.data-table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0 24px;
}

.data-table {
  width: 100%;
}

.complex-value {
  color: #999;
  font-style: italic;
  cursor: pointer;
}

.complex-value:hover {
  color: #409eff;
}
</style>
