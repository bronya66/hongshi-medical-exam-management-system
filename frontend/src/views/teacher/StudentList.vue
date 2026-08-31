<template>
  <div class="page-shell">

    <el-card class="page-card">
      <template #header>
        <div class="card-title">班级学员列表</div>
      </template>

      <div class="toolbar-wrap">
        <el-input
          v-model.trim="filter.keyword"
          placeholder="搜索姓名/专业/年级/班级"
          clearable
          style="width: 280px"
          @input="currentPage = 1"
        />
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="gender" label="性别" width="90" />
        <el-table-column prop="age" label="年龄" width="90" />
        <el-table-column prop="major" label="专业" min-width="160" />
        <el-table-column prop="grade" label="年级" width="120" />
        <el-table-column prop="class_name" label="班级" width="120" />
      </el-table>
      <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无学员" />
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
// 任课老师学员列表页面：仅查看自己班级学员

import { computed, onMounted, reactive, ref } from 'vue'
import { getTeacherStudentList } from '../../api/teacher'

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const filter = reactive({
  keyword: ''
})

const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  if (!keyword) return tableData.value
  return tableData.value.filter((item) => {
    const name = String(item.name || '').toLowerCase()
    const major = String(item.major || '').toLowerCase()
    const grade = String(item.grade || '').toLowerCase()
    const className = String(item.class_name || '').toLowerCase()
    return name.includes(keyword) || major.includes(keyword) || grade.includes(keyword) || className.includes(keyword)
  })
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getTeacherStudentList()
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
  currentPage.value = 1
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.toolbar-wrap {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
