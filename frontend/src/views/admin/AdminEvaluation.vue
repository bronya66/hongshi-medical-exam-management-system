<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>评价管理</div>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="学员姓名">
        <el-input v-model="query.student_name" placeholder="按学员姓名搜索" clearable />
      </el-form-item>
      <el-form-item label="老师姓名">
        <el-input v-model="query.teacher_name" placeholder="按老师姓名搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="student_name" label="学员姓名" width="120" />
      <el-table-column prop="teacher_name" label="老师姓名" width="120" />
      <el-table-column prop="score" label="评分" width="90" />
      <el-table-column prop="content" label="评价内容" min-width="200" />
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-wrap" v-if="filteredData.length">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        :total="filteredData.length"
      />
    </div>

    <el-dialog v-model="dialogVisible" title="编辑评价" width="620px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学员ID"><el-input v-model="form.student_id" /></el-form-item>
        <el-form-item label="老师ID"><el-input v-model="form.teacher_id" /></el-form-item>
        <el-form-item label="评分"><el-input v-model="form.score" /></el-form-item>
        <el-form-item label="评价内容"><el-input v-model="form.content" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteAdminEvaluationApi,
  getAdminEvaluationListApi,
  updateAdminEvaluationApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(8)
const dialogVisible = ref(false)
const isEdit = ref(true)
const currentId = ref(null)
const query = reactive({ student_name: '', teacher_name: '' })

const form = reactive({ student_id: '', teacher_id: '', score: '5', content: '' })

const filteredData = computed(() => {
  return tableData.value.filter((item) => {
    const studentHit = !query.student_name || String(item.student_name || '').includes(query.student_name)
    const teacherHit = !query.teacher_name || String(item.teacher_name || '').includes(query.teacher_name)
    return studentHit && teacherHit
  })
})

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

const handleSearch = () => {
  currentPage.value = 1
}

const parseDateTime = (value) => {
  if (!value) return 0
  const normalized = String(value)
    .replace(/年|\//g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, ' ')
    .trim()
  const timestamp = new Date(normalized).getTime()
  return Number.isNaN(timestamp) ? 0 : timestamp
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getAdminEvaluationListApi()
    const rows = res.data || []
    rows.sort((left, right) => parseDateTime(right.create_time) - parseDateTime(left.create_time))
    tableData.value = rows
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  currentId.value = row.id
  form.student_id = row.student_id
  form.teacher_id = row.teacher_id
  form.score = row.score
  form.content = row.content
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const payload = { ...form }
  await updateAdminEvaluationApi(currentId.value, payload)
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除评价 ID=${row.id}？`, '提示', { type: 'warning' })
  await deleteAdminEvaluationApi(row.id)
  ElMessage.success('删除成功')
  loadData()
}

loadData()
</script>

<style scoped>
.header-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mb12 {
  margin-bottom: 12px;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
