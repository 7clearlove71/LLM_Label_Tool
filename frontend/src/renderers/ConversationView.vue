<template>
  <div class="conversation-view">
    <div
      v-for="(msg, i) in messages"
      :key="i"
      class="message-bubble"
      :class="'role-' + msg.role"
    >
      <div class="role-label">{{ msg.role }}</div>
      <div class="content">{{ msg.content }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  messages: { type: Array, default: () => [] },
})
</script>

<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-bubble {
  border-radius: 8px;
  padding: 12px 16px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.role-system {
  background: #f5f5f5;
}
.role-system .role-label { color: #999; }

.role-user {
  background: #f0f9eb;
}
.role-user .role-label { color: #67c23a; }

.role-assistant {
  background: #ecf5ff;
}
.role-assistant .role-label { color: #409eff; }

.content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
