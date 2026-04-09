<template>
  <div class="pagination-bar">
    <span class="total-info">共 {{ total }} 条</span>
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="handlePageChange"
      small
    />
    <el-button
      v-if="!allLoaded"
      size="small"
      type="primary"
      link
      @click="$emit('load-all')"
    >
      加载全部
    </el-button>
    <span v-else class="all-loaded-tip">已加载全部</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  pageSize: { type: Number, default: 10 },
  allLoaded: { type: Boolean, default: false },
})

const emit = defineEmits(['page-change', 'load-all'])
const currentPage = ref(1)

function handlePageChange(page) {
  currentPage.value = page
  emit('page-change', (page - 1) * props.pageSize)
}

watch(() => props.total, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid #eee;
}

.total-info {
  color: #999;
  font-size: 13px;
}

.all-loaded-tip {
  color: #999;
  font-size: 12px;
}
</style>
