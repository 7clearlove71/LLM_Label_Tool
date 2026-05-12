<template>
  <div class="field-node" :style="{ paddingLeft: depth * 16 + 'px' }">
    <!-- 字段头 -->
    <div class="field-header" @click="toggle">
      <span v-if="isExpandable" class="expand-icon" :class="{ expanded }">›</span>
      <span v-else class="expand-placeholder" />
      <span class="key-label">{{ fieldKey }}</span>
      <span class="type-tag">{{ typeLabel }}</span>
      <span v-if="!isExpandable" class="value-inline">{{ inlineValue }}</span>
      <span v-else-if="!expanded" class="value-preview">{{ preview }}</span>
    </div>

    <!-- 展开内容 -->
    <div v-if="isExpandable && expanded" class="field-children">
      <!-- 数组 -->
      <template v-if="isArray">
        <div
          v-for="(item, i) in value"
          :key="i"
          class="array-item-wrapper"
        >
          <FieldNode
            v-if="isObject(item) || Array.isArray(item)"
            :field-key="'[' + i + ']'"
            :value="item"
            :depth="depth + 1"
          />
          <div v-else class="field-node" :style="{ paddingLeft: (depth + 1) * 16 + 'px' }">
            <div class="field-header">
              <span class="expand-placeholder" />
              <span class="key-label">[{{ i }}]</span>
              <span class="type-tag">{{ typeof item }}</span>
              <span class="value-inline">{{ formatPrimitive(item) }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 对象 -->
      <template v-else-if="isObjectType">
        <FieldNode
          v-for="(val, key) in value"
          :key="key"
          :field-key="String(key)"
          :value="val"
          :depth="depth + 1"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  fieldKey: { type: String, required: true },
  value: { type: [Object, Array, String, Number, Boolean, null], default: null },
  depth: { type: Number, default: 0 },
})

const expanded = ref(false)

const isArray = computed(() => Array.isArray(props.value))
const isObjectType = computed(() =>
  props.value !== null && typeof props.value === 'object' && !Array.isArray(props.value)
)
const isExpandable = computed(() => isArray.value || isObjectType.value)

const typeLabel = computed(() => {
  if (props.value === null || props.value === undefined) return 'null'
  if (isArray.value) return `array[${props.value.length}]`
  if (isObjectType.value) return `object{${Object.keys(props.value).length}}`
  return typeof props.value
})

const inlineValue = computed(() => {
  return formatPrimitive(props.value)
})

const preview = computed(() => {
  if (isArray.value) {
    if (props.value.length === 0) return '[]'
    return `[${props.value.length} 项]`
  }
  if (isObjectType.value) {
    const keys = Object.keys(props.value)
    if (keys.length === 0) return '{}'
    const shown = keys.slice(0, 3).join(', ')
    return `{ ${shown}${keys.length > 3 ? ', ...' : ''} }`
  }
  return ''
})

function toggle() {
  if (isExpandable.value) {
    expanded.value = !expanded.value
  }
}

function isObject(val) {
  return val !== null && typeof val === 'object'
}

function formatPrimitive(val) {
  if (val === null || val === undefined) return 'null'
  if (typeof val === 'string') {
    return `"${val}"`
  }
  if (typeof val === 'boolean') return val ? 'true' : 'false'
  return String(val)
}
</script>

<style scoped>
.field-node {
  font-size: 14px;
  font-family: var(--font-mono);
}

.field-header {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 5px 4px;
  border-radius: var(--rounded-sm);
  cursor: default;
  line-height: 1.4;
}

.field-header:hover {
  background: var(--apple-canvas-parchment);
}

.expand-icon {
  width: 16px;
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
  width: 16px;
  flex-shrink: 0;
}

.key-label {
  font-weight: 600;
  color: var(--apple-ink);
  flex-shrink: 0;
}

.type-tag {
  font-size: 11px;
  font-weight: 400;
  color: var(--apple-ink-muted-48);
  background: var(--apple-canvas-parchment);
  border-radius: var(--rounded-pill);
  padding: 0 6px;
  flex-shrink: 0;
  border: 1px solid var(--apple-divider-soft);
}

.value-inline {
  color: var(--apple-ink-muted-80);
  white-space: pre-wrap;
  word-break: break-word;
  min-width: 0;
}

.value-preview {
  color: var(--apple-ink-muted-48);
  font-style: italic;
  white-space: pre-wrap;
  word-break: break-word;
  min-width: 0;
}

.field-children {
  border-left: 1px solid var(--apple-divider-soft);
  margin-left: 11px;
}
</style>
