<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="数据详情"
    size="50%"
    :destroy-on-close="false"
    resizable
  >
    <template #header>
      <span>数据详情</span>
    </template>
    <template v-if="row">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="智能视图" name="smart">
          <SmartView :data="row" :schema="schema" />
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
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SmartView from '../renderers/SmartView.vue'
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

<style scoped>
:deep(.el-drawer) {
  border-left: 1px solid var(--apple-hairline);
  box-shadow: none !important;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 24px 16px;
}

:deep(.el-drawer__header span) {
  font-size: 21px;
  font-weight: 600;
  line-height: 1.19;
  letter-spacing: 0.231px;
  color: var(--apple-ink);
}

:deep(.el-drawer__body) {
  padding: 0 24px 24px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--apple-divider-soft);
}

:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: var(--apple-ink-muted-48);
}

:deep(.el-tabs__item.is-active) {
  font-weight: 600;
  color: var(--apple-ink);
}

:deep(.el-tabs__active-bar) {
  background-color: var(--apple-primary);
  height: 2px;
}
</style>
