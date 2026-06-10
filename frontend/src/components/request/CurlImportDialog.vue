<template>
  <el-dialog :model-value="modelValue" title="导入 curl" width="600px"
             @update:model-value="(v) => emit('update:modelValue', v)">
    <el-input v-model="text" type="textarea" :rows="8" placeholder="粘贴 curl 命令…" />
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="doImport">导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { parseCurl } from '../../api'

defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'imported'])

const text = ref('')
const loading = ref(false)

async function doImport() {
  if (!text.value.trim()) {
    ElMessage.warning('请粘贴 curl 命令')
    return
  }
  loading.value = true
  try {
    const { data } = await parseCurl(text.value)
    emit('imported', data)
    emit('update:modelValue', false)
    text.value = ''
  } catch (e) {
    ElMessage.error('解析失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>
