<template>
  <div class="file-tree">
    <el-tree
      v-if="treeData.length"
      :data="treeData"
      :props="treeProps"
      node-key="path"
      highlight-current
      :expand-on-click-node="false"
      @node-click="handleNodeClick"
    >
      <template #default="{ node, data }">
        <span class="tree-node">
          <span class="node-icon">{{ data.type === 'directory' ? '📁' : '📄' }}</span>
          <span class="node-label">{{ data.name }}</span>
          <span v-if="data.type === 'file'" class="node-size">
            {{ formatSize(data.size) }}
          </span>
        </span>
      </template>
    </el-tree>
    <div v-else class="empty-tip">请输入路径并扫描</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tree: { type: Object, default: null },
})

const emit = defineEmits(['select'])

const treeProps = {
  children: 'children',
  label: 'name',
  isLeaf: (data) => data.type === 'file',
}

const treeData = computed(() => {
  if (!props.tree) return []
  return props.tree.children || []
})

function handleNodeClick(data) {
  if (data.type === 'file') {
    emit('select', data.path)
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-tree {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xs);
}

.file-tree :deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: rgba(0, 0, 0, 0.04);
}

.file-tree :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: var(--rounded-sm);
  padding-left: 8px !important;
}

.file-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(0, 102, 204, 0.08);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: var(--apple-ink);
  width: 100%;
}

.node-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-size {
  color: var(--apple-ink-muted-48);
  font-size: 12px;
  letter-spacing: -0.12px;
  flex-shrink: 0;
}

.empty-tip {
  padding: var(--space-lg);
  text-align: center;
  color: var(--apple-ink-muted-48);
  font-size: 14px;
  letter-spacing: -0.224px;
}
</style>
