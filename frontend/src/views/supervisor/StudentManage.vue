<template>
  <div class="page-shell">

    <el-card class="page-card">
      <template #header>
        <div class="card-title">学员管理</div>
      </template>

      <el-form :model="query" :inline="true" label-width="72px" class="mb12">
        <el-form-item label="姓名">
          <el-input v-model="query.name" placeholder="按姓名搜索" clearable />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="query.className" placeholder="按班级筛选" clearable />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="query.major" placeholder="按专业筛选" clearable />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="query.grade" placeholder="按年级筛选" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table class="page-table" :data="pagedFilteredData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="gender" label="性别" width="90" />
        <el-table-column prop="age" label="年龄" width="90" />
        <el-table-column prop="major" label="专业" min-width="160" />
        <el-table-column prop="grade" label="年级" width="120" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="teacher_id" label="任课老师ID" width="120" />
        <el-table-column prop="teacher_username" label="任课老师账号" width="140" />
        <el-table-column label="操作" width="170">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && filteredData.length === 0" description="暂无学员" />
      <div class="pagination-wrap" v-if="filteredData.length > 0">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="filteredData.length"
          @current-change="handlePageChange"
        />
      </div>

      <el-dialog v-model="dialogVisible" title="编辑学员信息" width="640px">
        <el-form :model="editForm" label-width="88px">
          <el-form-item label="姓名">
            <el-input v-model="editForm.name" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="editForm.gender" style="width: 100%">
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
            </el-select>
          </el-form-item>
          <el-form-item label="年龄">
            <el-input-number v-model="editForm.age" :min="16" :max="60" />
          </el-form-item>
          <el-form-item label="专业">
            <el-input v-model="editForm.major" />
          </el-form-item>
          <el-form-item label="年级">
            <el-input v-model="editForm.grade" />
          </el-form-item>
          <el-form-item label="班级">
            <el-input v-model="editForm.class" />
          </el-form-item>
          <el-form-item label="老师ID">
            <el-input-number v-model="editForm.teacher_id" :min="1" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave">保存</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
// 督学学员管理页面：
// 1. 查询学员列表（后端支持 name/class）
// 2. 前端补充按专业、年级筛选
// 3. 编辑学员信息并提交

import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteSupervisorStudentApi, editSupervisorStudentApi, getSupervisorStudentList } from '../../api/supervisor'

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const query = reactive({
  name: '',
  className: '',
  major: '',
  grade: ''
})

const editForm = reactive({
  id: null,
  name: '',
  gender: '男',
  age: 22,
  major: '',
  grade: '',
  class: '',
  teacher_id: null
})

const filteredData = computed(() => {
  return tableData.value.filter((item) => {
    const majorMatch = !query.major || (item.major || '').includes(query.major)
    const gradeMatch = !query.grade || (item.grade || '').includes(query.grade)
    return majorMatch && gradeMatch
  })
})

const pagedFilteredData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

watch(filteredData, () => {
  currentPage.value = 1
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getSupervisorStudentList({ name: query.name, class: query.className })
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetQuery = () => {
  query.name = ''
  query.className = ''
  query.major = ''
  query.grade = ''
  loadData()
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.gender = row.gender || '男'
  editForm.age = row.age
  editForm.major = row.major
  editForm.grade = row.grade
  editForm.class = row.class_name
  editForm.teacher_id = row.teacher_id
  dialogVisible.value = true
}

const handleSave = async () => {
  await editSupervisorStudentApi({ ...editForm })
  ElMessage.success('编辑成功')
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除学员档案：${row.name}？`, '提示', { type: 'warning' })
  await deleteSupervisorStudentApi(row.id)
  ElMessage.success('删除成功')
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.mb12 {
  margin-bottom: 12px;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
