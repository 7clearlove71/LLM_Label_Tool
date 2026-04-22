<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="数据详情"
    size="50%"
    :destroy-on-close="false"
  >
    <template #header>
      <span>数据详情</span>
    </template>
    <template v-if="row">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="智能视图" name="smart">
          <ConversationView
            v-if="detectedPattern === 'conversation'"
            :messages="row.messages"
          />
          <PreferenceView
            v-else-if="detectedPattern === 'preference'"
            :data="row"
          />
          <InstructionView
            v-else-if="detectedPattern === 'instruction'"
            :data="row"
          />
          <JsonTreeView v-else :data="row" />
        </el-tab-pane>
        <el-tab-pane label="原始 JSON" name="json">
          <JsonTreeView :data="row" />
        </el-tab-pane>
        <el-tab-pane label="编辑" name="edit">
          <EditorView
            :data="row"
            @save="handleSave"
            @save-as="handleSaveAs"
          />
        </el-tab-pane>
      </el-tabs>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationView from '../renderers/ConversationView.vue'
import PreferenceView from '../renderers/PreferenceView.vue'
import InstructionView from '../renderers/InstructionView.vue'
import JsonTreeView from '../renderers/JsonTreeView.vue'
import EditorView from '../renderers/EditorView.vue'
import { updateRow, saveAs } from '../api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  row: { type: Object, default: null },
  rowIndex: { type: Number, default: 0 },
  schema: { type: Object, default: () => ({ fields: [] }) },
  filePath: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'saved', 'deleted'])

const activeTab = ref('smart')

const detectedPattern = computed(() => {
  if (!props.schema?.fields) return null
  for (const field of props.schema.fields) {
    if (field.pattern) return field.pattern
  }
  return null
})

async function handleSave(data) {
  await updateRow(props.filePath, props.rowIndex, data)
  ElMessage.success('保存成功')
  emit('saved')
}

async function handleSaveAs(data) {
  const { value: targetPath } = await ElMessageBox.prompt('输入目标文件路径', '另存为', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  })
  if (targetPath) {
    await updateRow(props.filePath, props.rowIndex, data)
    await saveAs(props.filePath, targetPath)
    ElMessage.success('另存为成功')
  }
}
</script>
