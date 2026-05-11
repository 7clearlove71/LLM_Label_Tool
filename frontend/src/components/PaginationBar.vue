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
  padding: var(--space-sm) var(--space-lg);
  border-top: 1px solid var(--apple-divider-soft);
}

.total-info {
  color: var(--apple-ink-muted-48);
  font-size: 14px;
  letter-spacing: -0.224px;
}

.pagination-bar :deep(.el-pagination) {
  --el-pagination-button-width: 32px;
  --el-pagination-button-height: 32px;
  --el-pagination-font-size: 13px;
}

.pagination-bar :deep(.el-pager li) {
  border-radius: var(--rounded-sm);
  background: var(--apple-surface-pearl);
  color: var(--apple-ink);
  font-weight: 400;
  min-width: 32px;
}

.pagination-bar :deep(.el-pager li.is-active) {
  background: var(--apple-primary);
  color: var(--apple-on-dark);
}

.pagination-bar :deep(.btn-prev),
.pagination-bar :deep(.btn-next) {
  border-radius: var(--rounded-sm);
  background: var(--apple-surface-pearl);
  color: var(--apple-ink-muted-48);
}

.all-loaded-tip {
  color: var(--apple-ink-muted-48);
  font-size: 12px;
  letter-spacing: -0.12px;
}

.pagination-bar :deep(.el-button--primary.is-link) {
  color: var(--apple-primary);
  font-size: 14px;
}
</style>
