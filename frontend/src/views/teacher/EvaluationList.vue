<template>
  <div class="page-shell">

    <el-card class="page-card">
      <template #header>
        <div class="header-wrap">
          <div class="card-title">学员评价列表</div>
          <el-tag type="success">平均分：{{ avgScore }}</el-tag>
        </div>
      </template>

      <div class="toolbar-wrap">
        <el-input
          v-model.trim="filter.keyword"
          placeholder="搜索学员账号/评价内容"
          clearable
          style="width: 280px"
          @input="currentPage = 1"
        />
        <el-select v-model="filter.scoreLevel" style="width: 140px" @change="currentPage = 1">
          <el-option label="全部评分" value="all" />
          <el-option label="1分" value="1" />
          <el-option label="2分" value="2" />
          <el-option label="3分" value="3" />
          <el-option label="4分" value="4" />
          <el-option label="5分" value="5" />
        </el-select>
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="student_username" label="学员账号" width="140" />
        <el-table-column prop="score" label="评分" width="100" />
        <el-table-column prop="content" label="评价内容" min-width="240" />
        <el-table-column prop="create_time" label="评价时间" width="180" />
      </el-table>
      <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无评价" />
      <div class="pagination-wrap" v-if="filteredTableData.length > 0">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="filteredTableData.length"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 任课老师评价列表页面：
// 1. 查看所有对自己的评价
// 2. 计算平均分

import { computed, onMounted, reactive, ref } from 'vue'
import { getTeacherEvaluationList } from '../../api/teacher'

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const filter = reactive({
  keyword: '',
  scoreLevel: 'all'
})

const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    const score = Number(item.score || 0)
    if (filter.scoreLevel !== 'all' && score !== Number(filter.scoreLevel)) return false

    if (!keyword) return true
    const student = String(item.student_username || '').toLowerCase()
    const content = String(item.content || '').toLowerCase()
    return student.includes(keyword) || content.includes(keyword)
  })
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const avgScore = computed(() => {
  if (!tableData.value.length) return '0.00'
  const total = tableData.value.reduce((sum, item) => sum + Number(item.score || 0), 0)
  return (total / tableData.value.length).toFixed(2)
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getTeacherEvaluationList()
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetFilter = () => {
  filter.keyword = ''
  filter.scoreLevel = 'all'
  currentPage.value = 1
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.header-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 700;
}

.toolbar-wrap {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
