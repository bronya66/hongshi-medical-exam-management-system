<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>学习资料管理</div>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="资料标题">
        <el-input v-model="query.title" placeholder="按标题搜索" clearable />
      </el-form-item>
      <el-form-item label="老师姓名">
        <el-input v-model="query.teacher_name" placeholder="按老师姓名搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="teacher_name" label="任课老师" width="130" />
      <el-table-column prop="title" label="资料标题" min-width="160" />
      <el-table-column prop="file_path" label="文件路径" min-width="220">
        <template #default="{ row }">{{ row.file_path ? row.file_path : '无附件' }}</template>
      </el-table-column>
      <el-table-column prop="video_url" label="视频链接" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ row.video_url ? row.video_url : '未设置' }}</template>
      </el-table-column>
      <el-table-column prop="download_count" label="下载次数" width="100" />
      <el-table-column prop="upload_time" label="上传时间" width="180" />
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

    <el-dialog v-model="dialogVisible" title="编辑资料" width="620px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任课老师ID"><el-input v-model="form.teacher_id" /></el-form-item>
        <el-form-item label="资料标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="文件路径"><el-input v-model="form.file_path" /></el-form-item>
        <el-form-item label="视频链接"><el-input v-model="form.video_url" /></el-form-item>
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
  deleteAdminMaterialsApi,
  getAdminMaterialsListApi,
  updateAdminMaterialsApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(8)
const dialogVisible = ref(false)
const isEdit = ref(true)
const currentId = ref(null)
const query = reactive({ title: '', teacher_name: '' })

const form = reactive({ teacher_id: '', title: '', file_path: '', video_url: '' })

const filteredData = computed(() => {
  return tableData.value.filter((item) => {
    const titleHit = !query.title || String(item.title || '').includes(query.title)
    const teacherHit = !query.teacher_name || String(item.teacher_name || '').includes(query.teacher_name)
    return titleHit && teacherHit
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
    const res = await getAdminMaterialsListApi()
    const rows = res.data || []
    rows.sort((left, right) => parseDateTime(right.upload_time) - parseDateTime(left.upload_time))
    tableData.value = rows
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  currentId.value = row.id
  form.teacher_id = row.teacher_id
  form.title = row.title
  form.file_path = row.file_path
  form.video_url = row.video_url || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const payload = { ...form }
  await updateAdminMaterialsApi(currentId.value, payload)
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除资料 ${row.title}？`, '提示', { type: 'warning' })
  await deleteAdminMaterialsApi(row.id)
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
