<template>
  <div class="smart-view">
    <div class="data-section">
      <FieldNode
        v-for="(value, key) in data"
        :key="key"
        :field-key="String(key)"
        :value="value"
        :depth="0"
      />
    </div>
  </div>
</template>

<script setup>
import FieldNode from './FieldNode.vue'

defineProps({
  data: { type: Object, default: () => ({}) },
  schema: { type: Object, default: () => ({ fields: [] }) },
})
</script>

<style scoped>
.smart-view {
  display: flex;
  flex-direction: column;
}

.data-section {
  display: flex;
  flex-direction: column;
}
</style>
