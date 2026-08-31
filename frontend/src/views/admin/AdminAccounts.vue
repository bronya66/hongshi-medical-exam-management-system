<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>管理员账号管理</div>
        <el-button type="primary" @click="openCreate">新增管理员</el-button>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="账号">
        <el-input v-model="query.username" placeholder="按账号搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="账号" width="180" />
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑管理员' : '新增管理员'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="账号"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码">
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
  createAdminAdminUserApi,
  deleteAdminAdminUserApi,
  getAdminAdminUsersApi,
  updateAdminAdminUserApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(8)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

const query = reactive({ username: '' })
const form = reactive({ username: '', password: '' })

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return tableData.value.slice(start, start + pageSize.value)
})

const resetForm = () => {
  form.username = ''
  form.password = ''
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
    const res = await getAdminAdminUsersApi({ ...query })
    const rows = res.data || []
    rows.sort((left, right) => parseDateTime(right.create_time) - parseDateTime(left.create_time))
    tableData.value = rows
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  currentId.value = null
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  form.username = row.username
  form.password = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const payload = { ...form }
  if (isEdit.value) {
    await updateAdminAdminUserApi(currentId.value, payload)
    ElMessage.success('更新成功')
  } else {
    await createAdminAdminUserApi(payload)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除管理员 ${row.username}？`, '提示', { type: 'warning' })
  await deleteAdminAdminUserApi(row.id)
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
