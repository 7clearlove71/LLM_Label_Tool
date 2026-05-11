<template>
  <div class="toolbar">
    <el-input
      v-model="keyword"
      placeholder="搜索内容..."
      clearable
      size="default"
      class="search-input"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <el-select
      v-model="selectedField"
      placeholder="全部字段"
      clearable
      size="default"
      class="field-select"
    >
      <el-option
        v-for="field in fields"
        :key="field.name"
        :label="field.name"
        :value="field.name"
      />
    </el-select>
    <button class="search-btn" @click="handleSearch">搜索</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['search'])
const keyword = ref('')
const selectedField = ref('')

function handleSearch() {
  emit('search', { keyword: keyword.value, field: selectedField.value || null })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  border-bottom: 1px solid var(--apple-divider-soft);
}

.search-input {
  width: 280px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: var(--rounded-pill);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
  height: 36px;
  padding: 0 16px;
}

.search-input :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px var(--apple-primary-focus);
}

.search-input :deep(.el-input__inner) {
  font-size: 14px;
  letter-spacing: -0.224px;
}

.search-input :deep(.el-input__prefix .el-icon) {
  color: var(--apple-ink-muted-48);
}

.field-select {
  width: 150px;
}

.field-select :deep(.el-input__wrapper) {
  border-radius: var(--rounded-md);
  background: var(--apple-surface-pearl);
  box-shadow: 0 0 0 1px var(--apple-divider-soft);
  height: 36px;
}

.field-select :deep(.el-input__inner) {
  font-size: 14px;
  letter-spacing: -0.224px;
}

.search-btn {
  height: 36px;
  padding: 0 20px;
  border: none;
  border-radius: var(--rounded-pill);
  background: var(--apple-primary);
  color: var(--apple-on-dark);
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}

.search-btn:hover {
  background: var(--apple-primary-focus);
}

.search-btn:active {
  transform: scale(0.95);
}
</style>
