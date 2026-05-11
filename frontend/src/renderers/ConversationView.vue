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
  gap: var(--space-sm);
}

.message-bubble {
  border-radius: var(--rounded-sm);
  padding: 14px 18px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0;
}

.role-system {
  background: var(--apple-canvas-parchment);
}
.role-system .role-label { color: var(--apple-ink-muted-48); }

.role-user {
  background: #f0f9eb;
}
.role-user .role-label { color: #67c23a; }

.role-assistant {
  background: #f0f4ff;
}
.role-assistant .role-label { color: var(--apple-primary); }

.content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
