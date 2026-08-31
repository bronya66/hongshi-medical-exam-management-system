<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>用户管理</div>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="账号">
        <el-input v-model="query.username" placeholder="按账号搜索" clearable />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="query.role" clearable placeholder="全部角色" style="width: 140px">
          <el-option label="学员" value="student" />
          <el-option label="任课老师" value="teacher" />
          <el-option label="督学老师" value="supervisor" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="账号" width="160" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">{{ getRoleLabel(row.role) }}</template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" min-width="180" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-wrap" v-if="tableData.length">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        :total="tableData.length"
      />
    </div>
    <el-empty v-if="!loading && tableData.length === 0" description="暂无用户" />

    <el-dialog v-model="dialogVisible" title="编辑用户" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="学员" value="student" />
            <el-option label="任课老师" value="teacher" />
            <el-option label="督学老师" value="supervisor" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" prop="">
          <el-input v-model="form.password" type="password" show-password placeholder="编辑时可留空表示不改" />
        </el-form-item>
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
  deleteAdminUserApi,
  getAdminUsersApi,
  updateAdminUserApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(12)
const dialogVisible = ref(false)
const currentId = ref(null)
const formRef = ref(null)

const query = reactive({ username: '', role: '' })
const form = reactive({ username: '', role: 'student', password: '' })

const roleLabelMap = {
  student: '学员',
  teacher: '任课老师',
  supervisor: '督学老师'
}

const getRoleLabel = (role) => roleLabelMap[role] || role

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return tableData.value.slice(start, start + pageSize.value)
})

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
    const res = await getAdminUsersApi({ ...query })
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
  form.username = row.username
  form.role = row.role
  form.password = ''
  dialogVisible.value = true
}

const handleSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    await updateAdminUserApi(currentId.value, { ...form })
    ElMessage.success('更新成功')

    dialogVisible.value = false
    loadData()
  })
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除账号 ${row.username}？`, '提示', { type: 'warning' })
  await deleteAdminUserApi(row.id)
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
