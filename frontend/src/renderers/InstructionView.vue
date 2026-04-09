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
  background: #f7f8fa;
  border-radius: 8px;
  padding: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.section-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
