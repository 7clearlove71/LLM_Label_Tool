<template>
  <div class="instruction-view">
    <div class="section">
      <div class="section-label">Instruction</div>
      <div class="section-content">{{ data.instruction }}</div>
    </div>
    <div class="section" v-if="data.input">
      <div class="section-label">Input</div>
      <div class="section-content">{{ data.input }}</div>
    </div>
    <div class="section">
      <div class="section-label">Output</div>
      <div class="section-content">{{ data.output }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: () => ({}) },
})
</script>

<style scoped>
.instruction-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section {
  background: var(--apple-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-ink-muted-48);
  text-transform: uppercase;
  margin-bottom: var(--space-xs);
  letter-spacing: -0.12px;
}

.section-content {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--apple-ink);
}
</style>
