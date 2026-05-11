<template>
  <div class="json-tree-view">
    <vue-json-pretty :data="data" :deep="3" :show-line="false" />
  </div>
</template>

<script setup>
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

const props = defineProps({
  data: { type: [Object, Array, String, Number], default: null },
})
</script>

<style scoped>
.json-tree-view {
  padding: var(--space-xs);
  font-size: 14px;
  letter-spacing: -0.224px;
}
</style>
