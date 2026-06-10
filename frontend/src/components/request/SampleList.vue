<template>
  <div class="sample-list">
    <div class="sl-header">
      <span>请求样例</span>
    </div>
    <div v-if="!samples.length" class="sl-empty">暂无样例</div>
    <div
      v-for="s in samples"
      :key="s.id"
      class="sl-item"
      :class="{ active: s.id === activeId }"
      @click="emit('load', s)"
    >
      <span class="sl-method">{{ s.request.method }}</span>
      <span class="sl-name">{{ s.name }}</span>
      <span class="sl-actions">
        <button class="sl-btn" @click.stop="rename(s)">改名</button>
        <button class="sl-btn del" @click.stop="emit('delete', s.id)">删</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

defineProps({
  samples: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['load', 'delete', 'rename'])

async function rename(s) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名', { inputValue: s.name })
    if (value && value.trim()) emit('rename', { id: s.id, name: value.trim() })
  } catch (e) { /* 取消 */ }
}
</script>

<style scoped>
.sample-list { display: flex; flex-direction: column; }
.sl-header { padding: 12px 14px; font-weight: 600; font-size: 13px; color: #555; }
.sl-empty { padding: 12px 14px; color: #aaa; font-size: 13px; }
.sl-item { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; border-radius: 8px; margin: 0 6px; }
.sl-item:hover { background: rgba(0,122,255,0.06); }
.sl-item.active { background: rgba(0,122,255,0.12); }
.sl-method { font-size: 11px; font-weight: 700; color: var(--apple-primary, #007aff); min-width: 38px; }
.sl-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sl-actions { display: none; gap: 6px; }
.sl-item:hover .sl-actions { display: flex; }
.sl-btn { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; }
.sl-btn.del:hover { color: #ff3b30; }
</style>
