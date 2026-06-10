<template>
  <div class="msg" :class="message.role">
    <div v-if="message.reasoning" class="msg-reasoning">
      <button class="mr-toggle" @click="expanded = !expanded">
        <span class="mr-caret" :class="{ open: expanded }">▸</span>
        思考过程{{ streaming ? '（进行中…）' : '' }}
      </button>
      <pre v-show="expanded" class="mr-body">{{ message.reasoning }}</pre>
    </div>
    <div v-if="message.content" class="msg-content">{{ message.content }}</div>
    <div v-else-if="streaming && !message.reasoning" class="msg-content typing">…</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: Object, required: true },
  // 流式中：reasoning 默认展开；结束后自动折叠
  streaming: { type: Boolean, default: false },
})

const expanded = ref(props.streaming)
watch(
  () => props.streaming,
  (s) => { if (!s) expanded.value = false; else expanded.value = true }
)
</script>

<style scoped>
.msg { display: flex; flex-direction: column; gap: 6px; margin: 10px 0; max-width: 80%; }
.msg.user { align-self: flex-end; align-items: flex-end; }
.msg.assistant, .msg.system { align-self: flex-start; align-items: flex-start; }
.msg-content { padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-content { background: var(--apple-primary, #007aff); color: #fff; }
.msg.assistant .msg-content { background: #f1f1f3; color: #1d1d1f; }
.msg.system .msg-content { background: #fff7e6; color: #8a6d3b; font-size: 13px; }
.msg-content.typing { color: #aaa; }
.msg-reasoning { width: 100%; }
.mr-toggle { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; padding: 2px 0; display: inline-flex; align-items: center; gap: 4px; }
.mr-caret { display: inline-block; transition: transform 0.15s; }
.mr-caret.open { transform: rotate(90deg); }
.mr-body { margin: 4px 0 0; padding: 10px 12px; background: #fafafa; border-left: 2px solid #ddd; border-radius: 6px; font-size: 12px; color: #666; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; }
</style>
