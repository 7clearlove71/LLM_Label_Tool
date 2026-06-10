<template>
  <div class="conv-list">
    <div class="cl-header">
      <span>对话</span>
      <button class="cl-btn" @click="emit('new')">+新对话</button>
    </div>
    <div v-if="!conversations.length" class="cl-empty">暂无对话</div>
    <div
      v-for="c in conversations" :key="c.id"
      class="cl-item" :class="{ active: c.id === activeId }"
      @click="emit('select', c.id)"
    >
      <span class="cl-name">{{ c.name }}</span>
      <span class="cl-actions">
        <button class="cl-btn" @click.stop="rename(c)">rename</button>
        <button class="cl-btn del" @click.stop="confirmDelete(c)">del</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

defineProps({
  conversations: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['new', 'select', 'rename', 'delete'])

async function rename(c) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名对话', { inputValue: c.name })
    if (value && value.trim()) emit('rename', { id: c.id, name: value.trim() })
  } catch (e) { /* 取消 */ }
}
async function confirmDelete(c) {
  try {
    await ElMessageBox.confirm(`确定删除对话「${c.name}」？`, '删除确认', { type: 'warning' })
    emit('delete', c.id)
  } catch (e) { /* 取消 */ }
}
</script>

<style scoped>
.conv-list { display: flex; flex-direction: column; }
.cl-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; font-weight: 600; font-size: 13px; color: #555; }
.cl-empty { padding: 10px 12px; color: #aaa; font-size: 13px; }
.cl-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; cursor: pointer; border-radius: 8px; margin: 0 6px; }
.cl-item:hover { background: rgba(0,122,255,0.06); }
.cl-item.active { background: rgba(0,122,255,0.12); }
.cl-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cl-actions { display: none; gap: 6px; }
.cl-item:hover .cl-actions { display: flex; }
.cl-btn { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; padding: 0; }
.cl-btn:hover { color: var(--apple-primary, #007aff); }
.cl-btn.del:hover { color: #ff3b30; }
</style>
