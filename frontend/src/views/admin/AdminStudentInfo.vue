<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>学员信息管理</div>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="姓名">
        <el-input v-model="query.name" placeholder="按姓名搜索" clearable />
      </el-form-item>
      <el-form-item label="专业">
        <el-input v-model="query.major" placeholder="按专业搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="gender" label="性别" width="100" />
      <el-table-column prop="age" label="年龄" width="90" />
      <el-table-column prop="major" label="专业" min-width="130" />
      <el-table-column prop="grade" label="年级" width="120" />
      <el-table-column prop="class_name" label="班级" width="120" />
      <el-table-column label="老师信息" min-width="320">
        <template #default="{ row }">
          <div>
            <div>老师ID：{{ (row.teacher_ids || []).join('、') || '-' }}</div>
            <div>老师姓名：{{ (row.teacher_names || []).join('、') || '-' }}</div>
          </div>
        </template>
      </el-table-column>
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

    <el-dialog v-model="dialogVisible" title="编辑学员档案" width="620px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄"><el-input v-model="form.age" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
        <el-form-item label="年级"><el-input v-model="form.grade" /></el-form-item>
        <el-form-item label="班级"><el-input v-model="form.class_name" /></el-form-item>
        <el-form-item label="任课老师ID"><el-input v-model="form.teacher_id" /></el-form-item>
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
  deleteAdminStudentInfoApi,
  getAdminStudentInfoListApi,
  updateAdminStudentInfoApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(12)
const dialogVisible = ref(false)
const currentId = ref(null)
const query = reactive({ name: '', major: '' })

const form = reactive({
  user_id: '',
  name: '',
  gender: '男',
  age: '',
  major: '',
  grade: '',
  class_name: '',
  teacher_id: ''
})

const filteredData = computed(() => {
  return tableData.value.filter((item) => {
    const nameHit = !query.name || String(item.name || '').includes(query.name)
    const majorHit = !query.major || String(item.major || '').includes(query.major)
    return nameHit && majorHit
  })
})

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

const handleSearch = () => {
  currentPage.value = 1
}

const resetForm = () => {
  form.user_id = ''
  form.name = ''
  form.gender = '男'
  form.age = ''
  form.major = ''
  form.grade = ''
  form.class_name = ''
  form.teacher_id = ''
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getAdminStudentInfoListApi()
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  currentId.value = row.id
  form.user_id = row.user_id
  form.name = row.name
  form.gender = row.gender
  form.age = row.age
  form.major = row.major
  form.grade = row.grade
  form.class_name = row.class_name
  form.teacher_id = row.teacher_id
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const payload = { ...form }
  await updateAdminStudentInfoApi(currentId.value, payload)
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除学员档案 ${row.name}？`, '提示', { type: 'warning' })
  await deleteAdminStudentInfoApi(row.id)
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
