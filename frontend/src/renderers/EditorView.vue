<template>
  <div class="editor-view">
    <el-input
      v-model="jsonText"
      type="textarea"
      :rows="20"
      class="json-editor"
      spellcheck="false"
    />
    <div v-if="parseError" class="error-tip">{{ parseError }}</div>
    <div class="editor-actions">
      <el-button type="primary" @click="handleSave" :disabled="!!parseError">
        保存
      </el-button>
      <el-button @click="handleSaveAs" :disabled="!!parseError">
        另存为
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: null },
})

const emit = defineEmits(['save', 'save-as'])

const jsonText = ref('')

watch(() => props.data, (val) => {
  jsonText.value = JSON.stringify(val, null, 2)
}, { immediate: true })

const parseError = computed(() => {
  try {
    JSON.parse(jsonText.value)
    return null
  } catch (e) {
    return 'JSON 格式错误: ' + e.message
  }
})

function handleSave() {
  const parsed = JSON.parse(jsonText.value)
  emit('save', parsed)
}

function handleSaveAs() {
  const parsed = JSON.parse(jsonText.value)
  emit('save-as', parsed)
}
</script>

<style scoped>
.editor-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.json-editor :deep(.el-textarea__inner) {
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.5;
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.error-tip {
  color: #f56c6c;
  font-size: 12px;
  letter-spacing: -0.12px;
}

.editor-actions {
  display: flex;
  gap: var(--space-xs);
}

.editor-actions :deep(.el-button--primary) {
  border-radius: var(--rounded-pill);
  padding: 10px 22px;
}

.editor-actions :deep(.el-button--default) {
  border-radius: var(--rounded-pill);
  padding: 10px 22px;
  color: var(--apple-primary);
  border-color: var(--apple-primary);
}

.editor-actions :deep(.el-button:active) {
  transform: scale(0.95);
}
</style>
