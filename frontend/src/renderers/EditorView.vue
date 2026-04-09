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
  gap: 12px;
}

.json-editor :deep(textarea) {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.error-tip {
  color: #f56c6c;
  font-size: 12px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}
</style>
