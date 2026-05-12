<template>
  <div class="schema-field-row" :style="{ paddingLeft: depth * 16 + 12 + 'px' }">
    <div class="field-line" @click="toggle">
      <span v-if="hasChildren" class="expand-icon" :class="{ expanded }">›</span>
      <span v-else class="expand-placeholder" />
      <span class="field-name">{{ field.name }}</span>
      <span class="field-type">{{ field.type }}</span>
      <span v-if="hasChildren" class="children-count">{{ field.children.length }} 个子字段</span>
    </div>
    <div v-if="hasChildren && expanded" class="field-children">
      <SchemaField
        v-for="child in field.children"
        :key="child.name"
        :field="child"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const expanded = ref(false)
const hasChildren = computed(() => props.field.children && props.field.children.length > 0)

function toggle() {
  if (hasChildren.value) {
    expanded.value = !expanded.value
  }
}
</script>

<style scoped>
.schema-field-row {
  font-size: 13px;
}

.field-line {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  cursor: default;
  border-radius: var(--rounded-sm);
}

.field-line:hover {
  background: rgba(0, 0, 0, 0.03);
}

.expand-icon {
  width: 12px;
  flex-shrink: 0;
  font-size: 14px;
  color: var(--apple-ink-muted-48);
  transition: transform 0.15s ease;
  transform: rotate(0deg);
  cursor: pointer;
  text-align: center;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  width: 12px;
  flex-shrink: 0;
}

.field-name {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--apple-ink);
}

.field-type {
  font-size: 11px;
  color: var(--apple-ink-muted-48);
  background: var(--apple-canvas);
  border-radius: var(--rounded-pill);
  padding: 0 6px;
  border: 1px solid var(--apple-hairline);
}

.children-count {
  font-size: 11px;
  color: var(--apple-ink-muted-48);
  margin-left: 2px;
}

.field-children {
  border-left: 1px solid var(--apple-divider-soft);
  margin-left: 17px;
}
</style>
