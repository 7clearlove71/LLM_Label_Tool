<template>
  <div class="schema-overview">
    <div class="schema-header" @click="expanded = !expanded">
      <span class="toggle-icon" :class="{ expanded }">›</span>
      <span class="schema-title">Schema</span>
      <span class="schema-badge">{{ fields.length }} 个字段</span>
    </div>
    <div v-if="expanded" class="schema-body">
      <SchemaField
        v-for="field in fields"
        :key="field.name"
        :field="field"
        :depth="0"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SchemaField from './SchemaField.vue'

const props = defineProps({
  schema: { type: Object, default: () => ({ fields: [] }) },
})

const expanded = ref(false)
const fields = computed(() => props.schema?.fields || [])
</script>

<style scoped>
.schema-overview {
  background: var(--apple-canvas-parchment);
  border-radius: var(--rounded-md);
  border: 1px solid var(--apple-divider-soft);
  overflow: hidden;
  margin: 12px 16px 0;
}

.schema-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}

.schema-header:hover {
  background: var(--apple-divider-soft);
}

.toggle-icon {
  font-size: 16px;
  color: var(--apple-ink-muted-48);
  transition: transform 0.2s ease;
  transform: rotate(0deg);
  flex-shrink: 0;
  width: 12px;
  text-align: center;
}

.toggle-icon.expanded {
  transform: rotate(90deg);
}

.schema-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.08px;
  color: var(--apple-ink-muted-48);
  text-transform: uppercase;
}

.schema-badge {
  font-size: 12px;
  color: var(--apple-ink-muted-48);
  background: var(--apple-canvas);
  border-radius: var(--rounded-pill);
  padding: 1px 8px;
  border: 1px solid var(--apple-hairline);
}
</style>
