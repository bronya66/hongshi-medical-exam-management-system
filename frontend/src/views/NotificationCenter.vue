<template>
  <div class="page-shell">
    <el-card class="page-card">
      <template #header>
        <div class="header-wrap">
          <div class="card-title">我的通知</div>
          <el-space>
            <el-tag type="warning">未读 {{ unreadCount }}</el-tag>
            <el-button text type="primary" @click="markAllRead">全部标记为已读</el-button>
          </el-space>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="系统通知" name="system" />
        <el-tab-pane label="作业通知" name="homework" />
        <el-tab-pane label="打卡通知" name="checkin" />
        <el-tab-pane label="资料通知" name="materials" />
        <el-tab-pane label="学习计划" name="learning_plan" />
        <el-tab-pane label="评价通知" name="evaluation" />
        <el-tab-pane label="考试通知" name="exam" />
      </el-tabs>

      <div v-loading="loading" class="notification-list">
        <div v-for="item in filteredList" :key="item.id" class="notification-card" :class="{ unread: !item.is_read }">
          <div class="notification-main">
            <div class="notification-title">{{ item.title }}</div>
            <div class="notification-content">{{ item.content }}</div>
            <div class="notification-meta">{{ item.create_time }}</div>
          </div>
          <div class="notification-actions">
            <el-tag size="small" :type="item.is_read ? 'info' : 'danger'">{{ item.is_read ? '已读' : '未读' }}</el-tag>
            <el-button v-if="!item.is_read" text type="primary" @click="markRead(item.id)">标记已读</el-button>
          </div>
        </div>
      </div>

      <el-empty v-if="filteredList.length === 0" description="当前分类暂无通知" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getNotificationListApi, markAllNotificationReadApi, markNotificationReadApi } from '../api/notification'

const activeTab = ref('all')
const loading = ref(false)
const list = ref([])

const tabMap = {
  all: 'all',
  system: 'system',
  homework: 'homework',
  checkin: 'checkin',
  materials: 'materials',
  learning_plan: 'learning_plan',
  evaluation: 'evaluation',
  exam: 'exam'
}

const filteredList = computed(() => {
  if (activeTab.value === 'all') return list.value
  return list.value.filter((item) => item.category === tabMap[activeTab.value])
})

const unreadCount = computed(() => list.value.filter((item) => !item.is_read).length)

const loadData = async () => {
  try {
    loading.value = true
    const res = await getNotificationListApi()
    list.value = res.data?.list || []
  } finally {
    loading.value = false
  }
}

const markRead = async (id) => {
  await markNotificationReadApi(id)
  ElMessage.success('已标记为已读')
  await loadData()
}

const markAllRead = async () => {
  await markAllNotificationReadApi()
  ElMessage.success('全部通知已标记为已读')
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.notification-list {
  display: grid;
  gap: 12px;
}

.notification-card {
  border: 1px solid #edf0f5;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.notification-card.unread {
  border-color: #91caff;
  background: #f6fbff;
}

.notification-title {
  font-size: 15px;
  font-weight: 700;
  color: #262626;
}

.notification-content {
  margin-top: 6px;
  color: #595959;
  line-height: 1.7;
}

.notification-meta {
  margin-top: 8px;
  color: #8c8c8c;
  font-size: 12px;
}

.notification-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

@media (max-width: 767px) {
  .notification-card {
    flex-direction: column;
  }

  .notification-actions {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
