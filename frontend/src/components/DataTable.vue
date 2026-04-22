<template>
  <div class="data-card-list">
    <div
      v-for="(row, i) in rows"
      :key="i"
      class="data-card"
      @click="handleRowClick(row, i)"
    >
      <div class="card-header">
        <span class="card-index">#{{ offset + i + 1 }}</span>
        <span class="card-expand-hint">点击查看详情 / 编辑</span>
      </div>
      <div class="card-body">
        <!-- 对话格式：直接展示 messages -->
        <template v-if="pattern === 'conversation' && row.messages">
          <div class="card-fields" v-if="simpleFields.length">
            <span v-for="f in simpleFields" :key="f" class="card-field-tag">
              <span class="field-name">{{ f }}:</span> {{ row[f] }}
            </span>
          </div>
          <div class="mini-conversation">
            <div
              v-for="(msg, mi) in row.messages.slice(0, 4)"
              :key="mi"
              class="mini-msg"
              :class="'role-' + msg.role"
            >
              <span class="mini-role">{{ msg.role }}</span>
              <span class="mini-content">{{ truncate(msg.content, 200) }}</span>
            </div>
            <div v-if="row.messages.length > 4" class="mini-more">
              ... 还有 {{ row.messages.length - 4 }} 条消息
            </div>
          </div>
        </template>

        <!-- 偏好格式：展示 chosen / rejected -->
        <template v-else-if="pattern === 'preference'">
          <div class="card-fields" v-if="simpleFields.length">
            <span v-for="f in simpleFields" :key="f" class="card-field-tag">
              <span class="field-name">{{ f }}:</span> {{ row[f] }}
            </span>
          </div>
          <div class="pref-preview">
            <div class="pref-side chosen">
              <span class="pref-label">✅ Chosen</span>
              <span class="pref-text">{{ truncate(formatValue(row.chosen), 150) }}</span>
            </div>
            <div class="pref-side rejected">
              <span class="pref-label">❌ Rejected</span>
              <span class="pref-text">{{ truncate(formatValue(row.rejected), 150) }}</span>
            </div>
          </div>
        </template>

        <!-- 指令格式：展示 instruction / input / output -->
        <template v-else-if="pattern === 'instruction'">
          <div class="instruction-preview">
            <div class="inst-section">
              <span class="inst-label">Instruction</span>
              <span class="inst-text">{{ truncate(row.instruction, 200) }}</span>
            </div>
            <div class="inst-section" v-if="row.input">
              <span class="inst-label">Input</span>
              <span class="inst-text">{{ truncate(row.input, 100) }}</span>
            </div>
            <div class="inst-section">
              <span class="inst-label">Output</span>
              <span class="inst-text">{{ truncate(row.output, 200) }}</span>
            </div>
          </div>
        </template>

        <!-- 通用格式：展示所有字段 -->
        <template v-else>
          <div class="generic-fields">
            <div v-for="key in Object.keys(row)" :key="key" class="generic-field">
              <span class="field-name">{{ key }}:</span>
              <span class="field-value">{{ truncate(formatValue(row[key]), 200) }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>
    <div v-if="!rows.length" class="no-data">暂无数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  schema: { type: Object, default: () => ({ fields: [] }) },
  offset: { type: Number, default: 0 },
})

const emit = defineEmits(['row-click'])

const pattern = computed(() => {
  if (!props.schema?.fields) return null
  for (const field of props.schema.fields) {
    if (field.pattern) return field.pattern
  }
  return null
})

const simpleFields = computed(() => {
  if (!props.schema?.fields) return []
  const skipKeys = new Set(['messages', 'chosen', 'rejected', 'instruction', 'input', 'output'])
  return props.schema.fields
    .filter(f => f.display === 'column' && !skipKeys.has(f.name))
    .map(f => f.name)
})

function handleRowClick(row, i) {
  emit('row-click', { row, index: props.offset + i })
}

function truncate(text, maxLen) {
  if (!text) return ''
  const s = String(text)
  return s.length > maxLen ? s.slice(0, maxLen) + '...' : s
}

function formatValue(val) {
  if (val === null || val === undefined) return ''
  if (typeof val === 'string') return val
  return JSON.stringify(val, null, 2)
}
</script>

<style scoped>
.data-card-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: #fff;
}

.data-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.card-index {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
}

.card-expand-hint {
  font-size: 11px;
  color: #c0c4cc;
}

.card-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.card-field-tag {
  font-size: 12px;
  color: #666;
  background: #f7f8fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.field-name {
  font-weight: 600;
  color: #999;
  margin-right: 4px;
}

/* 对话预览 */
.mini-conversation {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mini-msg {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.mini-role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-right: 8px;
}

.mini-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.role-system { background: #f5f5f5; }
.role-system .mini-role { color: #999; }

.role-user { background: #f0f9eb; }
.role-user .mini-role { color: #67c23a; }

.role-assistant { background: #ecf5ff; }
.role-assistant .mini-role { color: #409eff; }

.mini-more {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 4px;
}

/* 偏好预览 */
.pref-preview {
  display: flex;
  gap: 12px;
}

.pref-side {
  flex: 1;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.pref-side.chosen {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.pref-side.rejected {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.pref-label {
  font-size: 11px;
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.pref-text {
  white-space: pre-wrap;
  word-break: break-word;
}

/* 指令预览 */
.instruction-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.inst-section {
  background: #f7f8fa;
  border-radius: 6px;
  padding: 10px 12px;
}

.inst-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  display: block;
  margin-bottom: 4px;
}

.inst-text {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 通用字段 */
.generic-fields {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.generic-field {
  font-size: 13px;
  line-height: 1.5;
}

.field-value {
  white-space: pre-wrap;
  word-break: break-word;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 48px;
  font-size: 14px;
}
</style>
