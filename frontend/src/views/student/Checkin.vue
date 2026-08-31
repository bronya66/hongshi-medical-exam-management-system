<template>
  <div class="page-shell">

    <el-row :gutter="16">
      <el-col :span="11">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">打卡提交</div>
          </template>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
            <el-form-item label="打卡日期" prop="checkin_date">
              <el-date-picker
                v-model="form.checkin_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="请选择打卡日期"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="打卡内容" prop="content">
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="4"
                placeholder="请输入今日学习内容"
              />
            </el-form-item>

            <el-form-item label="打卡截图">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                :file-list="uploadFileList"
                :on-change="onFileChange"
                :on-remove="onFileRemove"
              >
                <el-button>选择文件</el-button>
              </el-upload>
              <div class="upload-tip">可上传任意格式文件</div>
            </el-form-item>

            <el-form-item v-if="uploadPercent > 0" label="上传进度">
              <el-progress :percentage="uploadPercent" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="submitCheckin">提交打卡</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="13">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">我的打卡记录</div>
          </template>
          <div class="toolbar-wrap">
            <el-input
              v-model.trim="recordFilter.keyword"
              placeholder="搜索打卡内容/日期"
              clearable
              style="width: 260px"
              @input="currentPage = 1"
            />
            <el-button @click="resetRecordFilter">重置</el-button>
          </div>
          <el-table class="page-table" :data="pagedRecords" border stripe table-layout="auto" v-loading="listLoading">
            <el-table-column prop="checkin_date" label="打卡日期" width="120" />
            <el-table-column prop="content" label="打卡内容" min-width="220" />
            <el-table-column label="截图" width="100">
              <template #default="{ row }">
                <el-button v-if="row.file_path" link type="primary" @click="openAttachmentPreview(row.file_path)">查看</el-button>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="提交时间" min-width="160" />
            <el-table-column label="操作" width="170">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!listLoading && filteredRecords.length === 0" description="暂无打卡记录" />
          <div class="pagination-wrap" v-if="filteredRecords.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredRecords.length"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <el-dialog v-model="dialogVisible" title="编辑打卡" width="560px">
    <el-form :model="editForm" label-width="90px">
      <el-form-item label="打卡日期">
        <el-date-picker v-model="editForm.checkin_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-form-item label="打卡内容">
        <el-input v-model="editForm.content" type="textarea" :rows="4" />
      </el-form-item>
      <el-form-item label="截图文件">
        <el-upload ref="editUploadRef" :auto-upload="false" :limit="1" :on-change="onEditFileChange" :on-remove="onEditFileRemove">
          <el-button>选择新截图</el-button>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
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
</template>

<script setup>
// 学员打卡页面：
// 1. 输入打卡内容
// 2. 上传截图
// 3. 调用 /api/student/checkin
// 4. 展示上传进度和成功失败提示

import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteStudentCheckinApi, getStudentCheckinListApi, studentCheckinApi, updateStudentCheckinApi } from '../../api/student'

const formRef = ref(null)
const uploadRef = ref(null)
const loading = ref(false)
const uploadPercent = ref(0)
const selectedFile = ref(null)
const uploadFileList = ref([])
const listLoading = ref(false)
const records = ref([])
const dialogVisible = ref(false)
const editUploadRef = ref(null)
const editFile = ref(null)
const attachmentDialogVisible = ref(false)
const attachmentUrl = ref('')
const attachmentPreviewType = ref('unsupported')
const currentPage = ref(1)
const pageSize = ref(8)
const recordFilter = reactive({
  keyword: ''
})

const editForm = reactive({
  id: null,
  checkin_date: '',
  content: ''
})

const form = reactive({
  checkin_date: new Date().toISOString().slice(0, 10),
  content: ''
})

const rules = {
  checkin_date: [{ required: true, message: '请选择打卡日期', trigger: 'change' }],
  content: [{ required: true, message: '请输入打卡内容', trigger: 'blur' }]
}

const filteredRecords = computed(() => {
  const keyword = recordFilter.keyword.toLowerCase()
  if (!keyword) return records.value
  return records.value.filter((item) => {
    const content = String(item.content || '').toLowerCase()
    const checkinDate = String(item.checkin_date || '').toLowerCase()
    const createTime = String(item.create_time || '').toLowerCase()
    return content.includes(keyword) || checkinDate.includes(keyword) || createTime.includes(keyword)
  })
})

const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

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

const onFileChange = (file, fileList) => {
  selectedFile.value = file.raw
  uploadFileList.value = fileList.slice(-1)
}

const onFileRemove = () => {
  selectedFile.value = null
  uploadFileList.value = []
}

const onEditFileChange = (file) => {
  editFile.value = file.raw
}

const onEditFileRemove = () => {
  editFile.value = null
}

const loadRecords = async () => {
  try {
    listLoading.value = true
    const res = await getStudentCheckinListApi()
    records.value = res.data || []
    currentPage.value = 1
  } finally {
    listLoading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetRecordFilter = () => {
  recordFilter.keyword = ''
  currentPage.value = 1
}

const submitCheckin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    const formData = new FormData()
    formData.append('checkin_date', form.checkin_date)
    formData.append('content', form.content)
    if (selectedFile.value) {
      formData.append('file', selectedFile.value)
    }

    try {
      loading.value = true
      uploadPercent.value = 0

      await studentCheckinApi(formData, (evt) => {
        if (!evt.total) return
        uploadPercent.value = Math.min(100, Math.round((evt.loaded / evt.total) * 100))
      })

      ElMessage.success('打卡成功')
      form.content = ''
      selectedFile.value = null
      uploadFileList.value = []
      uploadRef.value?.clearFiles?.()
      uploadPercent.value = 0
      loadRecords()
    } finally {
      loading.value = false
    }
  })
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.checkin_date = normalizeDateForApi(row.checkin_date)
  editForm.content = row.content
  editFile.value = null
  dialogVisible.value = true
}

const handleUpdate = async () => {
  const formData = new FormData()
  formData.append('checkin_date', editForm.checkin_date)
  formData.append('content', editForm.content)
  if (editFile.value) formData.append('file', editFile.value)
  await updateStudentCheckinApi(editForm.id, formData)
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadRecords()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除该打卡记录？', '提示', { type: 'warning' })
  await deleteStudentCheckinApi(row.id)
  ElMessage.success('删除成功')
  loadRecords()
}

loadRecords()
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.upload-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
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
