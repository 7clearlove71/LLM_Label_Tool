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
    <el-button @click="handleSearch" size="default" type="primary" plain>
      搜索
    </el-button>
    <el-button @click="$emit('save-as')" size="default" plain>
      另存为
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['search', 'save-as'])
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
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.search-input {
  width: 280px;
}

.field-select {
  width: 150px;
}
</style>
