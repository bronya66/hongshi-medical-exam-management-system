<template>
  <el-card>
    <template #header>
      <div class="header-wrap">
        <div>打卡管理</div>
      </div>
    </template>

    <el-form :inline="true" :model="query" class="mb12">
      <el-form-item label="学员姓名">
        <el-input v-model="query.student_name" placeholder="按学员姓名搜索" clearable />
      </el-form-item>
      <el-form-item label="打卡内容">
        <el-input v-model="query.content" placeholder="按内容搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="pagedData" border v-loading="loading">
      <el-table-column prop="student_name" label="学员姓名" width="120" />
      <el-table-column prop="content" label="打卡内容" min-width="180" />
      <el-table-column prop="file_path" label="截图路径" min-width="180">
        <template #default="{ row }">
          <el-button v-if="row.file_path" link type="primary" @click="openAttachmentPreview(row.file_path)">查看截图</el-button>
          <span v-else>无附件</span>
        </template>
      </el-table-column>
      <el-table-column prop="checkin_date" label="打卡日期" width="130" />
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

    <el-dialog v-model="dialogVisible" title="编辑打卡" width="620px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学员ID"><el-input v-model="form.student_id" /></el-form-item>
        <el-form-item label="打卡内容"><el-input v-model="form.content" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="截图路径"><el-input v-model="form.file_path" /></el-form-item>
        <el-form-item label="打卡日期">
          <el-date-picker v-model="form.checkin_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachmentDialogVisible" title="打卡截图预览" width="920px" destroy-on-close @closed="closeAttachmentDialog">
      <div class="attachment-wrap">
        <el-image
          v-if="attachmentPreviewType === 'image'"
          :src="attachmentUrl"
          fit="contain"
          class="attachment-image"
        />
        <iframe
          v-else-if="attachmentPreviewType === 'iframe'"
          :src="attachmentUrl"
          class="attachment-iframe"
          referrerpolicy="no-referrer"
        />
        <el-empty v-else description="当前格式不支持小窗预览，请点击新标签打开" />
      </div>
      <template #footer>
        <el-button type="primary" link @click="openAttachmentDirect">新标签打开</el-button>
        <el-button @click="closeAttachmentDialog">关闭</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteAdminCheckinApi,
  getAdminCheckinListApi,
  updateAdminCheckinApi
} from '../../api/admin'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(8)
const dialogVisible = ref(false)
const attachmentDialogVisible = ref(false)
const attachmentUrl = ref('')
const attachmentPreviewType = ref('unsupported')
const isEdit = ref(true)
const currentId = ref(null)
const query = reactive({ student_name: '', content: '' })

const form = reactive({ student_id: '', content: '', file_path: '', checkin_date: '' })

const filteredData = computed(() => {
  return tableData.value.filter((item) => {
    const studentHit = !query.student_name || String(item.student_name || '').includes(query.student_name)
    const contentHit = !query.content || String(item.content || '').includes(query.content)
    return studentHit && contentHit
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

const normalizeDateForApi = (value) => {
  if (!value) return ''
  const text = String(value).trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text

  const normalized = text
    .replace(/年|\//g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, '')
    .replace(/\s+/g, ' ')

  const parsed = new Date(normalized.replace(' ', 'T'))
  if (!Number.isNaN(parsed.getTime())) {
    const y = parsed.getFullYear()
    const m = String(parsed.getMonth() + 1).padStart(2, '0')
    const d = String(parsed.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }

  const matched = text.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日$/)
  if (matched) {
    const [, y, m, d] = matched
    return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  }

  return ''
}

const buildUploadUrl = (filePath) => {
  if (!filePath) return '#'
  const text = String(filePath).trim().replace(/[。；，、！）】》]+$/g, '')
  if (text.startsWith('http://') || text.startsWith('https://')) return text
  if (text.startsWith('/uploads/')) return text
  return `/uploads/${text}`
}

const getFileExtension = (url) => {
  if (!url) return ''
  try {
    const normalized = new URL(url, window.location.origin)
    const path = normalized.pathname || ''
    const idx = path.lastIndexOf('.')
    return idx >= 0 ? path.slice(idx).toLowerCase() : ''
  } catch {
    const clean = String(url).split('?')[0]
    const idx = clean.lastIndexOf('.')
    return idx >= 0 ? clean.slice(idx).toLowerCase() : ''
  }
}

const resolveAttachmentPreviewType = (url) => {
  const ext = getFileExtension(url)
  const imageExtSet = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'])
  const iframeExtSet = new Set(['.pdf', '.txt', '.md', '.html', '.htm'])
  if (imageExtSet.has(ext)) return 'image'
  if (iframeExtSet.has(ext)) return 'iframe'
  return 'unsupported'
}

const openInNewTabNoReferrer = (url) => {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.target = '_blank'
  anchor.rel = 'noopener noreferrer'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
}

const openAttachmentPreview = (filePath) => {
  const url = buildUploadUrl(filePath)
  if (!url || url === '#') {
    ElMessage.warning('当前无可预览截图')
    return
  }
  attachmentUrl.value = url
  attachmentPreviewType.value = resolveAttachmentPreviewType(url)
  attachmentDialogVisible.value = true
}

const openAttachmentDirect = () => {
  if (!attachmentUrl.value) return
  openInNewTabNoReferrer(attachmentUrl.value)
}

const closeAttachmentDialog = () => {
  attachmentDialogVisible.value = false
  attachmentUrl.value = ''
  attachmentPreviewType.value = 'unsupported'
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getAdminCheckinListApi()
    const rows = res.data || []
    rows.sort((left, right) => parseDateTime(right.create_time || right.checkin_date) - parseDateTime(left.create_time || left.checkin_date))
    tableData.value = rows
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  currentId.value = row.id
  form.student_id = row.student_id
  form.content = row.content
  form.file_path = row.file_path
  form.checkin_date = normalizeDateForApi(row.checkin_date)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const payload = { ...form }
  await updateAdminCheckinApi(currentId.value, payload)
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除打卡记录 ID=${row.id}？`, '提示', { type: 'warning' })
  await deleteAdminCheckinApi(row.id)
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

.attachment-wrap {
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
}

.attachment-image {
  width: 100%;
  max-height: 72vh;
}

.attachment-iframe {
  width: 100%;
  height: 72vh;
  border: none;
}
</style>
