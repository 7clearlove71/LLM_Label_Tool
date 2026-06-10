<template>
  <div class="request-builder">
    <div class="rb-line">
      <el-select :model-value="spec.method" style="width: 110px" @change="(v) => update('method', v)">
        <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
      </el-select>
      <el-input :model-value="spec.url" placeholder="请求 URL" class="rb-url" @input="(v) => update('url', v)" />
      <el-button type="primary" :loading="loading" @click="emit('send')">发送</el-button>
    </div>
    <div class="rb-tools">
      <button class="rb-tool" @click="emit('copy-curl')">复制为 curl</button>
      <span class="rb-save" v-if="saveState === 'saving'">保存中…</span>
      <span class="rb-save saved" v-else-if="saveState === 'saved'">已保存</span>
    </div>

    <el-tabs v-model="activeTab" class="rb-tabs">
      <el-tab-pane label="Params" name="params">
        <KeyValueEditor :model-value="spec.params" @update:model-value="(v) => update('params', v)" />
      </el-tab-pane>
      <el-tab-pane label="Headers" name="headers">
        <KeyValueEditor :model-value="spec.headers" @update:model-value="(v) => update('headers', v)" />
      </el-tab-pane>
      <el-tab-pane label="Body" name="body">
        <BodyEditor
          :body-type="spec.body_type" :body="spec.body" :form-body="spec.form_body"
          @update:body-type="(v) => update('body_type', v)"
          @update:body="(v) => update('body', v)"
          @update:form-body="(v) => update('form_body', v)"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import KeyValueEditor from './KeyValueEditor.vue'
import BodyEditor from './BodyEditor.vue'

const props = defineProps({
  spec: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  saveState: { type: String, default: '' },
})
const emit = defineEmits(['update:spec', 'send', 'copy-curl'])

const methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
const activeTab = ref('params')

function update(key, value) {
  emit('update:spec', { ...props.spec, [key]: value })
}
</script>

<style scoped>
.request-builder { display: flex; flex-direction: column; gap: 12px; }
.rb-line { display: flex; gap: 8px; }
.rb-url { flex: 1; }
.rb-tools { display: flex; align-items: center; gap: 14px; }
.rb-tool { border: none; background: none; color: var(--apple-primary, #007aff); cursor: pointer; font-size: 13px; }
.rb-save { font-size: 12px; color: #999; }
.rb-save.saved { color: #34c759; }
</style>
