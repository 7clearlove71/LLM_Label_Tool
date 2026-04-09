<template>
  <div class="path-input">
    <el-input
      v-model="path"
      placeholder="输入文件夹路径，如 /data/training"
      @keyup.enter="handleScan"
      size="default"
    >
      <template #append>
        <el-button @click="handleScan" :loading="loading">
          扫描
        </el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['scan'])
const path = ref('')
const loading = ref(false)

async function handleScan() {
  if (!path.value.trim()) return
  loading.value = true
  try {
    emit('scan', path.value.trim())
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.path-input {
  padding: 16px;
  border-bottom: 1px solid #eee;
}
</style>
