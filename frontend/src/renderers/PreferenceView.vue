<template>
  <div class="preference-view">
    <div class="pref-column chosen">
      <div class="pref-label">✅ Chosen</div>
      <div class="pref-content">{{ formatValue(data.chosen) }}</div>
    </div>
    <div class="pref-column rejected">
      <div class="pref-label">❌ Rejected</div>
      <div class="pref-content">{{ formatValue(data.rejected) }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

function formatValue(val) {
  if (typeof val === 'string') return val
  return JSON.stringify(val, null, 2)
}
</script>

<style scoped>
.preference-view {
  display: flex;
  gap: 16px;
}

.pref-column {
  flex: 1;
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.chosen {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.rejected {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.pref-label {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.224px;
  margin-bottom: var(--space-xs);
}

.pref-content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
