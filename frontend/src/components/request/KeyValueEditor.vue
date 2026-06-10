<template>
  <div class="kv-editor">
    <div v-for="(row, idx) in rows" :key="idx" class="kv-row">
      <el-checkbox v-model="row.enabled" @change="emitChange" />
      <el-input v-model="row.key" placeholder="Key" size="small" @input="emitChange" />
      <el-input v-model="row.value" placeholder="Value" size="small" @input="emitChange" />
      <button class="kv-del" @click="removeRow(idx)">✕</button>
    </div>
    <button class="kv-add" @click="addRow">+ 添加一行</button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])

const rows = ref(props.modelValue.map((r) => ({ ...r })))

watch(
  () => props.modelValue,
  (val) => {
    if (JSON.stringify(val) !== JSON.stringify(rows.value)) {
      rows.value = (val || []).map((r) => ({ ...r }))
    }
  }
)

function addRow() {
  rows.value.push({ key: '', value: '', enabled: true })
  emitChange()
}
function removeRow(i) {
  rows.value.splice(i, 1)
  emitChange()
}
function emitChange() {
  emit('update:modelValue', rows.value.map((r) => ({ ...r })))
}
</script>

<style scoped>
.kv-editor { display: flex; flex-direction: column; gap: 8px; padding: 8px 0; }
.kv-row { display: flex; align-items: center; gap: 8px; }
.kv-del { border: none; background: none; color: #999; cursor: pointer; }
.kv-del:hover { color: #ff3b30; }
.kv-add { align-self: flex-start; border: none; background: none; color: var(--apple-primary, #007aff); cursor: pointer; font-size: 13px; }
</style>
