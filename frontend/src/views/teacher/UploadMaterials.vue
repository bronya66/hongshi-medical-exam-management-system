<template>
  <div class="page-shell">

    <el-card class="page-card">
      <template #header>
        <div class="card-title">上传学习资料</div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px" style="max-width: 720px">
        <el-form-item label="资料标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入资料标题" />
        </el-form-item>

        <el-form-item label="视频链接">
          <el-input
            v-model.trim="form.video_url"
            placeholder="可选，支持 https://... 或 /uploads/materials/xxx.mp4"
          />
        </el-form-item>

        <el-form-item label="文件上传" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
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
          <el-button type="primary" :loading="loading" @click="handleUpload">上传资料</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="page-card" style="margin-top: 16px">
      <template #header>
        <div class="card-title">我的资料列表</div>
      </template>

      <el-form :inline="true" class="mb12">
        <el-form-item label="关键词">
          <el-input
            v-model.trim="materialFilter.keyword"
            placeholder="按标题或文件名筛选"
            style="width: 260px"
            @input="currentPage = 1"
          />
        </el-form-item>
      </el-form>

      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="listLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="资料标题" min-width="180" />
        <el-table-column label="文件" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <a class="file-link" :href="buildUploadUrl(row.file_path)" target="_blank" rel="noopener">{{ getFileName(row.file_path) }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="download_count" label="下载次数" width="100" />
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" @click="openFile(row)">查看</el-button>
              <el-button v-if="hasVideo(row)" size="small" type="success" @click="openVideo(row)">视频</el-button>
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!listLoading && filteredTableData.length === 0" description="暂无资料" />
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

    <el-dialog v-model="dialogVisible" title="编辑资料" width="620px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="资料标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="视频链接">
          <el-input
            v-model.trim="editForm.video_url"
            placeholder="可选，支持 https://... 或 /uploads/materials/xxx.mp4"
          />
        </el-form-item>
        <el-form-item label="替换文件">
          <el-upload
            ref="editUploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="onEditFileChange"
            :on-remove="onEditFileRemove"
          >
            <el-button>选择新文件</el-button>
          </el-upload>
          <div class="upload-tip">不选择则保持原文件，可上传任意格式文件</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="videoDialogVisible" :title="videoDialogTitle" width="860px" destroy-on-close @closed="closeVideoDialog">
      <div class="video-wrap">
        <iframe
          v-if="isExternalVideo && videoUrl"
          :src="videoUrl"
          class="video-iframe"
          referrerpolicy="no-referrer"
          allow="autoplay; fullscreen; picture-in-picture"
          allowfullscreen
        />
        <video v-else-if="videoUrl" :src="videoUrl" controls preload="metadata" class="video-player">
          您的浏览器不支持视频播放，请新标签打开观看。
        </video>
      </div>
      <template #footer>
        <el-button v-if="isExternalVideo && videoUrl" type="primary" link @click="openVideoDirect">新标签打开</el-button>
        <el-button @click="closeVideoDialog">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="materialDialogVisible" :title="materialDialogTitle" width="920px" destroy-on-close @closed="closeMaterialDialog">
      <div class="material-wrap">
        <el-image
          v-if="materialPreviewType === 'image'"
          :src="materialUrl"
          fit="contain"
          class="material-image"
        />
        <iframe
          v-else-if="materialPreviewType === 'iframe'"
          :src="materialUrl"
          class="material-iframe"
          referrerpolicy="no-referrer"
        />
        <el-empty v-else description="当前格式不支持小窗预览，请点击新标签打开" />
      </div>
      <template #footer>
        <el-button type="primary" link @click="openMaterialDirect">新标签打开</el-button>
        <el-button @click="closeMaterialDialog">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 任课老师资料上传页面：
// 1. 填写标题并选择文件
// 2. 调用 /api/teacher/upload_materials
// 3. 展示上传进度

import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteTeacherMaterialsApi, getTeacherMaterialsListApi, updateTeacherMaterialsApi, uploadMaterialsApi } from '../../api/teacher'

const formRef = ref(null)
const uploadRef = ref(null)
const editUploadRef = ref(null)
const loading = ref(false)
const listLoading = ref(false)
const uploadPercent = ref(0)
const selectedFile = ref(null)
const editSelectedFile = ref(null)
const tableData = ref([])
const dialogVisible = ref(false)
const videoDialogVisible = ref(false)
const videoUrl = ref('')
const videoDialogTitle = ref('资料视频')
const isExternalVideo = ref(false)
const materialDialogVisible = ref(false)
const materialDialogTitle = ref('资料预览')
const materialUrl = ref('')
const materialPreviewType = ref('unsupported')
const currentPage = ref(1)
const pageSize = ref(10)
const materialFilter = reactive({
  keyword: ''
})

const editForm = reactive({
  id: null,
  title: '',
  video_url: ''
})

const form = reactive({
  title: '',
  video_url: ''
})

const filteredTableData = computed(() => {
  const keyword = materialFilter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    if (!keyword) return true
    const title = String(item.title || '').toLowerCase()
    const fileName = getFileName(item.file_path).toLowerCase()
    return title.includes(keyword) || fileName.includes(keyword)
  })
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const rules = {
  title: [{ required: true, message: '请输入资料标题', trigger: 'blur' }]
}

const validateFile = (file) => {
  if (!file) {
    ElMessage.warning('文件无效，请重新选择')
    return false
  }

  return true
}

const onFileChange = (file) => {
  if (!validateFile(file.raw)) {
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    return
  }
  selectedFile.value = file.raw
}

const onFileRemove = () => {
  selectedFile.value = null
}

const onEditFileChange = (file) => {
  if (!validateFile(file.raw)) {
    editUploadRef.value?.clearFiles()
    editSelectedFile.value = null
    return
  }
  editSelectedFile.value = file.raw
}

const onEditFileRemove = () => {
  editSelectedFile.value = null
}

const handleUpload = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    if (!selectedFile.value) {
      ElMessage.warning('请先选择文件')
      return
    }

    const formData = new FormData()
    formData.append('title', form.title)
    if (form.video_url) {
      formData.append('video_url', form.video_url)
    }
    formData.append('file', selectedFile.value)

    try {
      loading.value = true
      uploadPercent.value = 0

      await uploadMaterialsApi(formData, (evt) => {
        if (!evt.total) return
        uploadPercent.value = Math.min(100, Math.round((evt.loaded / evt.total) * 100))
      })

      ElMessage.success('资料上传成功')
      form.title = ''
      form.video_url = ''
      selectedFile.value = null
      uploadPercent.value = 0
      uploadRef.value?.clearFiles()
      await loadData()
    } finally {
      loading.value = false
    }
  })
}

const loadData = async () => {
  try {
    listLoading.value = true
    const res = await getTeacherMaterialsListApi()
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    listLoading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.title = row.title
  editForm.video_url = row.video_url || ''
  editSelectedFile.value = null
  dialogVisible.value = true
  nextTick(() => {
    editUploadRef.value?.clearFiles()
  })
}

const handleUpdate = async () => {
  if (!editForm.title.trim()) {
    ElMessage.warning('资料标题不能为空')
    return
  }

  const replacedFile = Boolean(editSelectedFile.value)
  const formData = new FormData()
  formData.append('title', editForm.title)
  formData.append('video_url', editForm.video_url || '')
  if (editSelectedFile.value) {
    formData.append('file', editSelectedFile.value)
  }

  await updateTeacherMaterialsApi(editForm.id, formData)
  ElMessage.success(replacedFile ? '资料与文件已更新' : '资料标题已更新')
  dialogVisible.value = false
  editSelectedFile.value = null
  editUploadRef.value?.clearFiles()
  await loadData()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除资料：${row.title}？`, '提示', { type: 'warning' })
  await deleteTeacherMaterialsApi(row.id)
  ElMessage.success('删除成功')
  await loadData()
}

const buildUploadUrl = (filePath) => {
  if (!filePath) return '#'
  const text = String(filePath).trim().replace(/[。；，、！）】》]+$/g, '')
  if (text.startsWith('http://') || text.startsWith('https://')) return text
  if (text.startsWith('/uploads/')) return text
  return `/uploads/${text}`
}

const getFileName = (filePath) => {
  if (!filePath) return '未命名文件'
  const raw = String(filePath)
  const parts = raw.split('/')
  return parts[parts.length - 1] || raw
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

const isExternalHttpUrl = (url) => {
  if (!url) return false
  if (!(url.startsWith('http://') || url.startsWith('https://'))) return false
  try {
    const parsed = new URL(url)
    return parsed.origin !== window.location.origin
  } catch {
    return true
  }
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

const resolveMaterialPreviewType = (url) => {
  const ext = getFileExtension(url)
  const imageExtSet = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'])
  const iframeExtSet = new Set(['.pdf', '.txt', '.md', '.html', '.htm'])
  if (imageExtSet.has(ext)) return 'image'
  if (iframeExtSet.has(ext)) return 'iframe'
  return 'unsupported'
}

const openFile = (row) => {
  const url = buildUploadUrl(row.file_path)
  if (url === '#') {
    ElMessage.warning('当前资料无可访问文件')
    return
  }
  materialDialogTitle.value = row?.title ? `资料预览：${row.title}` : '资料预览'
  materialUrl.value = url
  materialPreviewType.value = resolveMaterialPreviewType(url)
  materialDialogVisible.value = true
}

const hasVideo = (row) => Boolean(String(row?.video_url || '').trim())

const openVideo = (row) => {
  const rawUrl = String(row?.video_url || '').trim()
  const url = buildUploadUrl(rawUrl)
  if (!url) {
    ElMessage.warning('当前资料未配置视频链接')
    return
  }
  videoDialogTitle.value = row?.title ? `视频资料：${row.title}` : '资料视频'
  isExternalVideo.value = isExternalHttpUrl(url)
  videoUrl.value = url
  videoDialogVisible.value = true
}

const closeVideoDialog = () => {
  videoDialogVisible.value = false
  videoUrl.value = ''
  videoDialogTitle.value = '资料视频'
  isExternalVideo.value = false
}

const openVideoDirect = () => {
  if (!videoUrl.value) return
  openInNewTabNoReferrer(videoUrl.value)
}

const closeMaterialDialog = () => {
  materialDialogVisible.value = false
  materialDialogTitle.value = '资料预览'
  materialUrl.value = ''
  materialPreviewType.value = 'unsupported'
}

const openMaterialDirect = () => {
  if (!materialUrl.value) return
  openInNewTabNoReferrer(materialUrl.value)
}

onMounted(loadData)
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.mb12 {
  margin-bottom: 12px;
}

.upload-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.file-link {
  color: #409eff;
  text-decoration: none;
}

.file-link:hover {
  text-decoration: underline;
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

.video-wrap {
  background: #000;
  border-radius: 10px;
  overflow: hidden;
}

.video-player {
  width: 100%;
  max-height: 72vh;
  display: block;
}

.video-iframe {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
  background: #000;
}

.material-wrap {
  min-height: 320px;
}

.material-iframe {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
  background: #fff;
}

.material-image {
  width: 100%;
  max-height: 72vh;
}
</style>
