<template>
  <div class="body-editor">
    <el-radio-group :model-value="bodyType" size="small" @change="onTypeChange">
      <el-radio-button value="none">none</el-radio-button>
      <el-radio-button value="json">JSON</el-radio-button>
      <el-radio-button value="raw">raw</el-radio-button>
      <el-radio-button value="form">form</el-radio-button>
    </el-radio-group>

    <div v-if="bodyType === 'json' || bodyType === 'raw'" class="body-text">
      <el-input
        :model-value="body"
        type="textarea"
        :rows="10"
        :placeholder="bodyType === 'json' ? 'JSON 请求体' : '原始请求体'"
        @input="(v) => emit('update:body', v)"
      />
    </div>

    <div v-else-if="bodyType === 'form'" class="body-form">
      <KeyValueEditor :model-value="formBody" @update:model-value="(v) => emit('update:formBody', v)" />
    </div>
  </div>
</template>

<script setup>
import KeyValueEditor from './KeyValueEditor.vue'

defineProps({
  bodyType: { type: String, default: 'none' },
  body: { type: String, default: '' },
  formBody: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:bodyType', 'update:body', 'update:formBody'])

function onTypeChange(v) {
  emit('update:bodyType', v)
}
</script>

<style scoped>
.body-editor { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
.body-text :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
</style>
