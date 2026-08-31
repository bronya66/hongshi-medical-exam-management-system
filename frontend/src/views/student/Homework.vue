<template>
  <div class="page-shell">
    <el-card class="page-card">
      <template #header>
        <div class="card-title">作业中心</div>
      </template>

      <div class="overview-strip">
        <div class="overview-item total">
          <div class="overview-label">作业总数</div>
          <div class="overview-value">{{ overviewStats.total }}</div>
        </div>
        <div class="overview-item submitted">
          <div class="overview-label">已提交</div>
          <div class="overview-value">{{ overviewStats.submitted }}</div>
        </div>
        <div class="overview-item pending">
          <div class="overview-label">待提交</div>
          <div class="overview-value">{{ overviewStats.pending }}</div>
        </div>
        <div class="overview-item expired">
          <div class="overview-label">已截止</div>
          <div class="overview-value">{{ overviewStats.expired }}</div>
        </div>
      </div>

      <div class="toolbar-wrap">
        <el-input
          v-model.trim="filter.keyword"
          placeholder="搜索作业标题/内容/老师"
          clearable
          style="width: 300px"
          @input="currentPage = 1"
        />
        <el-select v-model="filter.submitStatus" style="width: 150px" @change="currentPage = 1">
          <el-option label="全部状态" value="all" />
          <el-option label="已提交" value="submitted" />
          <el-option label="未提交" value="unsubmitted" />
        </el-select>
        <el-button plain @click="resetFilter">重置</el-button>
      </div>

      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading" :row-class-name="getRowClassName">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="teacher_name" label="任课老师" width="110" />
        <el-table-column prop="title" label="作业标题" min-width="170" show-overflow-tooltip />
        <el-table-column v-if="!isMobile" prop="content" label="作业内容" min-width="200" show-overflow-tooltip />
        <el-table-column v-if="!isMobile" prop="publish_time" label="发布时间" width="170" />
        <el-table-column label="截止时间" width="180">
          <template #default="{ row }">
            <div>{{ row.deadline || '-' }}</div>
            <div class="deadline-meta" :class="getDeadlineMeta(row).className">{{ getDeadlineMeta(row).text }}</div>
          </template>
        </el-table-column>
        <el-table-column label="提交状态" width="140">
          <template #default="{ row }">
            <el-tag :type="isHomeworkExpired(row) ? 'danger' : row.submission_id ? 'success' : 'info'" effect="light" round>
              {{ isHomeworkExpired(row) ? '已截止' : row.submission_id ? '已提交' : '未提交' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="老师评分" width="110">
          <template #default="{ row }">
            <span v-if="row.submission_id && row.submission_score !== null && row.submission_score !== undefined">
              {{ row.submission_score }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column v-if="!isMobile" label="老师评语" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.submission_id && row.submission_feedback">{{ row.submission_feedback }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-wrap">
              <el-button link @click="openDetail(row)">查看详情</el-button>
              <el-button link type="primary" :disabled="isHomeworkExpired(row)" @click="openSubmit(row)">{{ row.submission_id ? '修改提交' : '提交作业' }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无作业" />
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

    <el-dialog v-model="dialogVisible" title="作业提交" width="640px">
      <el-form :model="submitForm" label-width="90px">
        <el-form-item label="作业标题">
          <el-input :model-value="currentTitle" disabled />
        </el-form-item>
        <el-form-item label="提交内容">
          <el-input v-model="submitForm.content" type="textarea" :rows="4" placeholder="请输入作业提交说明" />
        </el-form-item>
        <el-form-item label="提交附件">
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="onFileChange" :on-remove="onFileRemove">
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item v-if="uploadPercent > 0" label="上传进度">
          <el-progress :percentage="uploadPercent" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" width="760px" class="detail-dialog">
      <template #header>
        <div class="detail-header">
          <div class="detail-title">{{ detailHomework?.title || '作业详情' }}</div>
          <div class="detail-tags">
            <el-tag :type="detailStatusTag.type" effect="light" round>{{ detailStatusTag.text }}</el-tag>
            <el-tag type="info" effect="plain" round>{{ detailHomework?.teacher_name || '未知老师' }}</el-tag>
          </div>
        </div>
      </template>

      <el-row :gutter="10" class="detail-metrics">
        <el-col :xs="24" :sm="8">
          <div class="metric-card">
            <div class="metric-label">发布时间</div>
            <div class="metric-value">{{ detailHomework?.publish_time || '-' }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="metric-card">
            <div class="metric-label">截止时间</div>
            <div class="metric-value">{{ detailHomework?.deadline || '-' }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="metric-card score" :class="detailScoreMeta.className">
            <div class="metric-label">老师评分</div>
            <div class="metric-value">{{ detailScoreMeta.value }}</div>
            <div class="metric-tip">{{ detailScoreMeta.level }}</div>
          </div>
        </el-col>
      </el-row>

      <div class="detail-section">
        <div class="section-title">作业要求</div>
        <div class="detail-prewrap">{{ detailHomework?.content || '-' }}</div>
        <div class="section-links">
          <el-link
            v-if="detailHomework?.homework_file_path"
            type="primary"
            @click="openAttachmentPreview(detailHomework.homework_file_path, '作业附件预览')"
          >查看作业附件</el-link>
          <span v-else class="link-empty">无作业附件</span>
        </div>
      </div>

      <div class="detail-section">
        <div class="section-title">我的提交</div>
        <div class="detail-prewrap">{{ detailHomework?.submission_content || '你还没有提交该作业。' }}</div>
        <div class="section-links">
          <el-link
            v-if="detailHomework?.submission_file_path"
            type="primary"
            @click="openAttachmentPreview(detailHomework.submission_file_path, '我的附件预览')"
          >查看我的附件</el-link>
          <span v-else class="link-empty">无提交附件</span>
        </div>
      </div>

      <div class="detail-section">
        <div class="section-title">老师反馈</div>
        <div class="detail-prewrap">{{ detailHomework?.submission_feedback || '老师暂未填写评语。' }}</div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" :disabled="isHomeworkExpired(detailHomework || {})" @click="openSubmit(detailHomework)">
          {{ detailHomework?.submission_id ? '去修改提交' : '去提交作业' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachmentDialogVisible" :title="attachmentDialogTitle" width="920px" destroy-on-close @closed="closeAttachmentDialog">
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
  </div>
</template>

<script setup>
// 学员作业页：查看任课老师发布的作业

import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getStudentHomeworkList, submitStudentHomeworkApi } from '../../api/student'

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const filter = reactive({
  keyword: '',
  submitStatus: 'all'
})
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const submitLoading = ref(false)
const uploadPercent = ref(0)
const uploadRef = ref(null)
const currentHomeworkId = ref(null)
const currentTitle = ref('')
const selectedFile = ref(null)
const isMobile = ref(false)
const detailHomework = ref(null)
const attachmentDialogVisible = ref(false)
const attachmentDialogTitle = ref('附件预览')
const attachmentUrl = ref('')
const attachmentPreviewType = ref('unsupported')

const submitForm = reactive({
  content: ''
})

const parseDateTime = (value) => {
  if (!value) return 0
  const text = String(value).trim()
  if (!text) return 0

  const normalized = text
    .replace(/年|\//g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, '')
    .replace(/\s+/g, ' ')

  const ts = new Date(normalized.replace(' ', 'T')).getTime()
  return Number.isFinite(ts) ? ts : 0
}

const isHomeworkExpired = (row) => {
  const deadlineTs = parseDateTime(row?.deadline)
  return deadlineTs > 0 && Date.now() > deadlineTs
}

const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    const isSubmitted = !!item.submission_id
    if (filter.submitStatus === 'submitted' && !isSubmitted) return false
    if (filter.submitStatus === 'unsubmitted' && isSubmitted) return false

    if (!keyword) return true
    const title = String(item.title || '').toLowerCase()
    const content = String(item.content || '').toLowerCase()
    const teacherName = String(item.teacher_name || '').toLowerCase()
    return title.includes(keyword) || content.includes(keyword) || teacherName.includes(keyword)
  })
})

const overviewStats = computed(() => {
  const source = filteredTableData.value
  const total = source.length
  const submitted = source.filter((item) => !!item.submission_id).length
  const expired = source.filter((item) => isHomeworkExpired(item)).length
  const pending = Math.max(0, total - submitted)
  return { total, submitted, pending, expired }
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getStudentHomeworkList()
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const getDeadlineMeta = (row) => {
  const deadlineTs = parseDateTime(row?.deadline)
  if (!deadlineTs) return { text: '未设置截止时间', className: 'info' }
  const remainHours = Math.ceil((deadlineTs - Date.now()) / 3600000)
  if (remainHours < 0) return { text: '已截止', className: 'danger' }
  if (remainHours <= 24) return { text: `剩余${remainHours}小时`, className: 'warning' }
  const remainDays = Math.ceil(remainHours / 24)
  return { text: `剩余${remainDays}天`, className: 'safe' }
}

const getRowClassName = ({ row }) => {
  return isHomeworkExpired(row) ? 'row-expired' : ''
}

const detailStatusTag = computed(() => {
  const row = detailHomework.value || {}
  if (isHomeworkExpired(row)) return { text: '已截止', type: 'danger' }
  if (row.submission_id) return { text: '已提交', type: 'success' }
  return { text: '待提交', type: 'warning' }
})

const detailScoreMeta = computed(() => {
  const score = detailHomework.value?.submission_score
  if (score === null || score === undefined || score === '') {
    return { value: '-', level: '暂无评分', className: 'empty' }
  }
  const numericScore = Number(score)
  if (Number.isNaN(numericScore)) {
    return { value: String(score), level: '已评分', className: 'normal' }
  }
  if (numericScore >= 90) return { value: numericScore, level: '优秀', className: 'excellent' }
  if (numericScore >= 75) return { value: numericScore, level: '良好', className: 'good' }
  if (numericScore >= 60) return { value: numericScore, level: '及格', className: 'normal' }
  return { value: numericScore, level: '待提升', className: 'warn' }
})

const updateViewportFlag = () => {
  isMobile.value = window.innerWidth <= 1200
}

const resetFilter = () => {
  filter.keyword = ''
  filter.submitStatus = 'all'
  currentPage.value = 1
}

const openSubmit = (row) => {
  if (isHomeworkExpired(row)) {
    ElMessage.warning('作业已过截止时间，不能提交')
    return
  }
  currentHomeworkId.value = row.id
  currentTitle.value = row.title
  submitForm.content = row.submission_content || ''
  selectedFile.value = null
  uploadPercent.value = 0
  uploadRef.value?.clearFiles()
  dialogVisible.value = true
}

const openDetail = (row) => {
  detailHomework.value = row
  detailDialogVisible.value = true
}

const buildHomeworkContentText = (row) => {
  const lines = [
    `作业标题：${row?.title || '-'}`,
    `任课老师：${row?.teacher_name || '-'}`,
    `发布时间：${row?.publish_time || '-'}`,
    `截止时间：${row?.deadline || '-'}`,
    '',
    '作业要求：',
    String(row?.content || '暂无作业内容').trim()
  ]
  return `${lines.join('\r\n')}\r\n`
}

const openHomeworkContent = (row) => {
  if (row?.homework_file_path) {
    window.open(`/uploads/${row.homework_file_path}`, '_blank')
    return
  }
  const content = buildHomeworkContentText(row)
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const blobUrl = URL.createObjectURL(blob)
  window.open(blobUrl, '_blank')
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 30000)
}

const buildUploadUrl = (filePath) => {
  if (!filePath) return ''
  const text = String(filePath).trim().replace(/[。；，、！）】》]+$/g, '')
  if (text.startsWith('http://') || text.startsWith('https://')) return text
  if (text.startsWith('/uploads/')) return text
  return `/uploads/${text}`
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

const openAttachmentPreview = (filePath, title = '附件预览') => {
  const url = buildUploadUrl(filePath)
  if (!url) {
    ElMessage.warning('当前无可预览附件')
    return
  }
  attachmentDialogTitle.value = title
  attachmentUrl.value = url
  attachmentPreviewType.value = resolveAttachmentPreviewType(url)
  attachmentDialogVisible.value = true
}

const closeAttachmentDialog = () => {
  attachmentDialogVisible.value = false
  attachmentDialogTitle.value = '附件预览'
  attachmentUrl.value = ''
  attachmentPreviewType.value = 'unsupported'
}

const openAttachmentDirect = () => {
  if (!attachmentUrl.value) return
  openInNewTabNoReferrer(attachmentUrl.value)
}

const onFileChange = (file) => {
  selectedFile.value = file.raw
}

const onFileRemove = () => {
  selectedFile.value = null
}

const handleSubmit = async () => {
  if (!currentHomeworkId.value) return

  const formData = new FormData()
  formData.append('homework_id', String(currentHomeworkId.value))
  formData.append('content', submitForm.content || '')
  if (selectedFile.value) {
    formData.append('file', selectedFile.value)
  }

  try {
    submitLoading.value = true
    uploadPercent.value = 0
    await submitStudentHomeworkApi(formData, (evt) => {
      if (!evt.total) return
      uploadPercent.value = Math.min(100, Math.round((evt.loaded / evt.total) * 100))
    })
    ElMessage.success('作业提交成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  updateViewportFlag()
  window.addEventListener('resize', updateViewportFlag)
  loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateViewportFlag)
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.overview-item {
  border-radius: 12px;
  padding: 10px 14px;
  color: #0b1220;
  background: linear-gradient(135deg, #f8fafc, #eef2ff);
  border: 1px solid #dbe4ff;
}

.overview-item.total {
  background: linear-gradient(135deg, #ecfeff, #e0f2fe);
  border-color: #bae6fd;
}

.overview-item.submitted {
  background: linear-gradient(135deg, #ecfdf3, #dcfce7);
  border-color: #bbf7d0;
}

.overview-item.pending {
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border-color: #fed7aa;
}

.overview-item.expired {
  background: linear-gradient(135deg, #fff1f2, #ffe4e6);
  border-color: #fecdd3;
}

.overview-label {
  font-size: 13px;
  color: #475569;
}

.overview-value {
  margin-top: 6px;
  font-size: 24px;
  line-height: 1;
  font-weight: 700;
}

.toolbar-wrap {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.detail-prewrap {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.detail-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-wrap {
  min-height: 320px;
}

.attachment-iframe {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
  background: #fff;
}

.attachment-image {
  width: 100%;
  max-height: 72vh;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-metrics {
  margin-bottom: 12px;
}

.metric-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 10px 12px;
  min-height: 76px;
}

.metric-card.score {
  background: linear-gradient(135deg, #eff6ff, #eef2ff);
}

.metric-label {
  font-size: 12px;
  color: #64748b;
}

.metric-value {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.metric-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #475569;
}

.metric-card.excellent .metric-value {
  color: #15803d;
}

.metric-card.good .metric-value {
  color: #1d4ed8;
}

.metric-card.warn .metric-value {
  color: #dc2626;
}

.detail-section {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
  padding: 12px;
  margin-bottom: 10px;
}

.section-title {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.section-links {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.link-empty {
  color: #94a3b8;
  font-size: 13px;
}

.action-wrap {
  display: flex;
  gap: 8px;
  align-items: center;
}

.deadline-meta {
  font-size: 12px;
  margin-top: 2px;
}

.deadline-meta.info {
  color: #64748b;
}

.deadline-meta.safe {
  color: #16a34a;
}

.deadline-meta.warning {
  color: #d97706;
}

.deadline-meta.danger {
  color: #dc2626;
}

:deep(.row-expired) {
  background-color: #fff7f7;
}

@media (max-width: 900px) {
  .overview-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-title {
    white-space: normal;
  }
}
</style>
