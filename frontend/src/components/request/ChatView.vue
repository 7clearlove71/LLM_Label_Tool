<template>
  <div class="chat-view">
    <div ref="scrollEl" class="cv-scroll">
      <div v-if="!messages.length" class="cv-empty">开始你的第一轮对话</div>
      <MessageBubble
        v-for="(m, i) in messages" :key="i"
        :message="m"
        :streaming="streaming && i === messages.length - 1 && m.role === 'assistant'"
      />
    </div>
    <div class="cv-input">
      <el-input
        v-model="draft" type="textarea" :rows="3" resize="none"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
        @keydown.enter="onEnter"
      />
      <div class="cv-actions">
        <el-button v-if="streaming" type="danger" plain @click="emit('stop')">停止</el-button>
        <el-button v-else type="primary" :disabled="!draft.trim()" @click="onSend">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  streaming: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'stop'])

const draft = ref('')
const scrollEl = ref(null)

function onSend() {
  const text = draft.value.trim()
  if (!text || props.streaming) return
  emit('send', text)
  draft.value = ''
}
function onEnter(e) {
  if (e.shiftKey) return
  e.preventDefault()
  onSend()
}

function scrollToBottom() {
  nextTick(() => {
    const el = scrollEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.cv-scroll { flex: 1; overflow: auto; display: flex; flex-direction: column; padding: 12px 16px; }
.cv-empty { margin: auto; color: #aaa; font-size: 14px; }
.cv-input { border-top: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.cv-actions { display: flex; justify-content: flex-end; }
</style>
