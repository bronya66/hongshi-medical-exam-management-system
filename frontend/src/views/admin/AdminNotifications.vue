<template>
  <div class="page-shell">
    <el-card class="page-card">
      <template #header>
        <div class="header-wrap">
          <div class="card-title">后台通知</div>
          <el-space>
            <el-tag type="danger">待处理 {{ pendingCount }}</el-tag>
            <el-button text type="primary" @click="markAllProcessed">全部标记已处理</el-button>
          </el-space>
        </div>
      </template>

      <el-table class="page-table" :data="tableData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="levelTypeMap[row.level] || 'info'">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="content" label="内容" min-width="240" />
        <el-table-column prop="create_time" label="时间" width="170" />
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'success' : 'danger'">{{ row.is_read ? '已处理' : '待处理' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="primary" :disabled="row.is_read" @click="markProcessed(row.id)">设为已处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getAdminNotificationListApi,
  markAdminNotificationReadApi,
  markAllAdminNotificationReadApi
} from '../../api/notification'

const levelTypeMap = {
  danger: 'danger',
  warning: 'warning',
  info: 'info'
}

const loading = ref(false)
const tableData = ref([])

const pendingCount = computed(() => tableData.value.filter((item) => !item.is_read).length)

const loadData = async () => {
  try {
    loading.value = true
    const res = await getAdminNotificationListApi()
    tableData.value = res.data?.list || []
  } finally {
    loading.value = false
  }
}

const markProcessed = async (id) => {
  await markAdminNotificationReadApi(id)
  ElMessage.success('已处理')
  await loadData()
}

const markAllProcessed = async () => {
  await markAllAdminNotificationReadApi()
  ElMessage.success('全部通知已处理')
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-table :deep(.el-button.is-text) {
  padding: 0;
}
</style>
