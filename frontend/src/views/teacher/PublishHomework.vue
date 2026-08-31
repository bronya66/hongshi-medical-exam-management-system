<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :span="24" :lg="10">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">发布作业</div>
          </template>

          <el-alert class="mb12" type="info" show-icon :closable="false" title="发布后学员端将立即可见，建议标题中包含课程关键词。" />

          <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
            <el-form-item label="作业标题" prop="title">
              <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="例如：西医临床-心血管病例分析（第3周）" />
            </el-form-item>

            <el-form-item label="作业内容" prop="content">
              <el-input v-model="form.content" type="textarea" :rows="5" placeholder="请输入任务说明、评分标准与提交要求" />
            </el-form-item>

            <el-form-item label="截止时间" prop="deadline">
              <el-date-picker
                v-model="form.deadline"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="请选择截止时间"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="作业附件">
              <el-upload
                class="homework-upload"
                :auto-upload="false"
                :limit="1"
                :file-list="homeworkFileList"
                :on-change="onHomeworkFileChange"
                :on-remove="onHomeworkFileRemove"
              >
                <el-button type="primary" plain>选择文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">可选附件，发布后学员可在作业列表查看并下载。</div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handlePublish">发布作业</el-button>
              <el-button @click="resetPublishForm">清空</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="24" :lg="14">
        <el-card class="page-card board-card">
          <template #header>
            <div class="card-title">数据总览 / 教学看板</div>
          </template>

          <div class="overview-grid">
            <div class="overview-item">
              <div class="summary-label">作业总数</div>
              <div class="summary-value">{{ summary.homeworkTotal }}</div>
            </div>
            <div class="overview-item">
              <div class="summary-label">进行中作业</div>
              <div class="summary-value">{{ summary.activeHomework }}</div>
            </div>
            <div class="overview-item">
              <div class="summary-label">提交总数</div>
              <div class="summary-value">{{ summary.submissionTotal }}</div>
            </div>
            <div class="overview-item">
              <div class="summary-label">已评分率</div>
              <div class="summary-value">{{ summary.gradedRate }}%</div>
            </div>
          </div>

          <div class="board-splitter"></div>

          <div class="teacher-summary-grid">
            <div class="summary-item">
              <div class="summary-label">本周发布</div>
              <div class="summary-value">{{ summary.thisWeekHomework }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">已截止作业</div>
              <div class="summary-value">{{ summary.expiredHomework }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">管理学员数</div>
              <div class="summary-value">{{ summary.studentTotal }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">平均分</div>
              <div class="summary-value">{{ summary.avgScore }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="page-card" style="margin-top: 16px">
      <template #header>
        <div class="card-title">作业列表</div>
      </template>

      <el-form :inline="true" class="mb12">
        <el-form-item label="关键词">
          <el-input v-model.trim="homeworkFilter.keyword" placeholder="按标题或内容筛选" style="width: 220px" @input="homeworkPage = 1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="homeworkFilter.status" style="width: 160px" @change="homeworkPage = 1">
            <el-option label="全部" value="all" />
            <el-option label="进行中" value="active" />
            <el-option label="已截止" value="expired" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table class="page-table" :data="pagedHomeworkData" border stripe table-layout="auto" v-loading="listLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="作业标题" min-width="180" />
        <el-table-column prop="content" label="作业内容" min-width="240" show-overflow-tooltip />
        <el-table-column label="附件" width="120">
          <template #default="{ row }">
            <el-button v-if="row.file_path" link type="primary" @click="openAttachmentPreview(row.file_path, `${row.title} - 作业附件`)">查看附件</el-button>
            <span v-else>无附件</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="isExpired(row.deadline) ? 'danger' : 'success'">{{ isExpired(row.deadline) ? '已截止' : '进行中' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="170" />
        <el-table-column prop="deadline" label="截止时间" width="170" />
        <el-table-column label="提交进度" width="180">
          <template #default="{ row }">
            <span>{{ getSubmissionStatText(row.id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!listLoading && filteredHomeworkData.length === 0" description="暂无作业" />
      <div class="pagination-wrap" v-if="filteredHomeworkData.length > 0">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="homeworkPage"
          :page-size="homeworkPageSize"
          :total="filteredHomeworkData.length"
          @current-change="handleHomeworkPageChange"
        />
      </div>
    </el-card>

    <el-card class="page-card" style="margin-top: 16px">
      <template #header>
        <div class="card-title">学员提交列表 / 评分</div>
      </template>

      <el-form :inline="true" class="mb12">
        <el-form-item label="按作业筛选">
          <el-select v-model="submissionFilter.homeworkId" clearable placeholder="全部作业" style="width: 240px" @change="submissionPage = 1">
            <el-option v-for="item in tableData" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="评分状态">
          <el-select v-model="submissionFilter.scoreStatus" style="width: 160px" @change="submissionPage = 1">
            <el-option label="全部" value="all" />
            <el-option label="待评分" value="pending" />
            <el-option label="已评分" value="graded" />
          </el-select>
        </el-form-item>
        <el-form-item label="学员账号">
          <el-input v-model.trim="submissionFilter.studentKeyword" placeholder="输入账号筛选" style="width: 180px" @input="submissionPage = 1" />
        </el-form-item>
      </el-form>

      <el-table class="page-table" :data="pagedSubmissionData" border stripe table-layout="auto" v-loading="submissionLoading">
        <el-table-column prop="id" label="提交ID" width="90" />
        <el-table-column prop="homework_title" label="作业标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="student_username" label="学员账号" width="140" />
        <el-table-column prop="content" label="提交内容" min-width="220" show-overflow-tooltip />
        <el-table-column label="附件" width="120">
          <template #default="{ row }">
            <el-button v-if="row.file_path" link type="primary" @click="openAttachmentPreview(row.file_path, `${row.student_username || '学员'} - 提交附件`)">查看附件</el-button>
            <span v-else>无附件</span>
          </template>
        </el-table-column>
        <el-table-column prop="submit_time" label="提交时间" width="170" />
        <el-table-column label="是否逾期" width="100">
          <template #default="{ row }">
            <el-tag :type="isLateSubmission(row) ? 'danger' : 'success'">{{ isLateSubmission(row) ? '逾期' : '按时' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="110">
          <template #default="{ row }">
            <el-tag v-if="hasScore(row)" type="success">{{ row.score }}</el-tag>
            <el-tag v-else type="warning">待评分</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="feedback" label="评语" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openReview(row)">评分</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!submissionLoading && filteredSubmissionData.length === 0" description="暂无学员提交" />
      <div class="pagination-wrap" v-if="filteredSubmissionData.length > 0">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="submissionPage"
          :page-size="submissionPageSize"
          :total="filteredSubmissionData.length"
          @current-change="handleSubmissionPageChange"
        />
      </div>
    </el-card>
  </div>

  <el-dialog v-model="dialogVisible" title="编辑作业" width="620px">
    <el-form :model="editForm" label-width="90px">
      <el-form-item label="作业标题">
        <el-input v-model="editForm.title" />
      </el-form-item>
      <el-form-item label="作业内容">
        <el-input v-model="editForm.content" type="textarea" :rows="4" />
      </el-form-item>
      <el-form-item label="截止时间">
        <el-date-picker v-model="editForm.deadline" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
      </el-form-item>
      <el-form-item label="当前附件">
        <el-button v-if="editForm.file_path" link type="primary" @click="openAttachmentPreview(editForm.file_path, '当前附件预览')">查看当前附件</el-button>
        <span v-else>无附件</span>
      </el-form-item>
      <el-form-item label="替换附件">
        <el-upload
          class="homework-upload"
          :auto-upload="false"
          :limit="1"
          :file-list="editHomeworkFileList"
          :on-change="onEditHomeworkFileChange"
          :on-remove="onEditHomeworkFileRemove"
        >
          <el-button type="primary" plain>选择新附件</el-button>
        </el-upload>
      </el-form-item>
      <el-form-item label="附件操作">
        <el-checkbox v-model="editForm.clear_file">清除当前附件</el-checkbox>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="reviewDialogVisible" title="作业评分" width="620px">
    <el-form :model="reviewForm" label-width="90px">
      <el-form-item label="作业标题">
        <el-input :model-value="reviewForm.homework_title" disabled />
      </el-form-item>
      <el-form-item label="学员账号">
        <el-input :model-value="reviewForm.student_username" disabled />
      </el-form-item>
      <el-form-item label="评分(0-100)">
        <el-input-number v-model="reviewForm.score" :min="0" :max="100" />
      </el-form-item>
      <el-form-item label="评语">
        <el-input v-model="reviewForm.feedback" type="textarea" :rows="4" placeholder="请输入评分评语" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="reviewDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleReview">保存</el-button>
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
</template>

<script setup>
// 任课老师发布作业页面

import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTeacherStudentList,
  deleteTeacherHomeworkApi,
  getTeacherHomeworkListApi,
  getTeacherHomeworkSubmissionListApi,
  publishHomeworkApi,
  reviewTeacherHomeworkSubmissionApi,
  updateTeacherHomeworkApi
} from '../../api/teacher'

const formRef = ref(null)
const loading = ref(false)
const listLoading = ref(false)
const submissionLoading = ref(false)
const updateLoading = ref(false)
const reviewLoading = ref(false)
const tableData = ref([])
const submissionTableData = ref([])
const teacherStudentCount = ref(0)
const dialogVisible = ref(false)
const reviewDialogVisible = ref(false)
const attachmentDialogVisible = ref(false)
const attachmentDialogTitle = ref('附件预览')
const attachmentUrl = ref('')
const attachmentPreviewType = ref('unsupported')
const homeworkFileList = ref([])
const homeworkFile = ref(null)
const editHomeworkFileList = ref([])
const editHomeworkFile = ref(null)
const homeworkPage = ref(1)
const homeworkPageSize = ref(8)
const submissionPage = ref(1)
const submissionPageSize = ref(8)

const homeworkFilter = reactive({
  keyword: '',
  status: 'all'
})

const submissionFilter = reactive({
  homeworkId: null,
  scoreStatus: 'all',
  studentKeyword: ''
})

const submissionStatMap = ref({})

const summary = computed(() => {
  const now = Date.now()
  const weekMs = 7 * 24 * 60 * 60 * 1000
  const expiredHomework = tableData.value.filter((item) => isExpired(item.deadline)).length
  const thisWeekHomework = tableData.value.filter((item) => {
    const ts = parseTime(item.publish_time)
    return ts > 0 && now - ts <= weekMs
  }).length

  const submissionTotal = submissionTableData.value.length
  const gradedRows = submissionTableData.value.filter((item) => hasScore(item))
  const gradedRate = submissionTotal ? Number(((gradedRows.length / submissionTotal) * 100).toFixed(1)) : 0
  const avgScore = gradedRows.length
    ? Number((gradedRows.reduce((sum, item) => sum + Number(item.score || 0), 0) / gradedRows.length).toFixed(1))
    : 0

  return {
    homeworkTotal: tableData.value.length,
    activeHomework: tableData.value.length - expiredHomework,
    expiredHomework,
    thisWeekHomework,
    studentTotal: teacherStudentCount.value,
    submissionTotal,
    gradedRate,
    avgScore
  }
})

const form = reactive({
  title: '',
  content: '',
  deadline: ''
})

const editForm = reactive({
  id: null,
  title: '',
  content: '',
  deadline: '',
  file_path: '',
  clear_file: false
})

const reviewForm = reactive({
  id: null,
  homework_title: '',
  student_username: '',
  score: 0,
  feedback: ''
})

const rules = {
  title: [{ required: true, message: '请输入作业标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入作业内容', trigger: 'blur' }],
  deadline: [{ required: true, message: '请选择截止时间', trigger: 'change' }]
}

const filteredHomeworkData = computed(() => {
  const keyword = homeworkFilter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    if (homeworkFilter.status === 'active' && isExpired(item.deadline)) return false
    if (homeworkFilter.status === 'expired' && !isExpired(item.deadline)) return false
    if (!keyword) return true
    const title = String(item.title || '').toLowerCase()
    const content = String(item.content || '').toLowerCase()
    return title.includes(keyword) || content.includes(keyword)
  })
})

const pagedHomeworkData = computed(() => {
  const start = (homeworkPage.value - 1) * homeworkPageSize.value
  return filteredHomeworkData.value.slice(start, start + homeworkPageSize.value)
})

const filteredSubmissionData = computed(() => {
  const studentKeyword = submissionFilter.studentKeyword.toLowerCase()
  return submissionTableData.value.filter((item) => {
    if (submissionFilter.homeworkId && Number(item.homework_id) !== Number(submissionFilter.homeworkId)) return false
    if (submissionFilter.scoreStatus === 'graded' && !hasScore(item)) return false
    if (submissionFilter.scoreStatus === 'pending' && hasScore(item)) return false
    if (!studentKeyword) return true
    return String(item.student_username || '').toLowerCase().includes(studentKeyword)
  })
})

const pagedSubmissionData = computed(() => {
  const start = (submissionPage.value - 1) * submissionPageSize.value
  return filteredSubmissionData.value.slice(start, start + submissionPageSize.value)
})

const parseTime = (value) => {
  if (!value) return 0
  if (value instanceof Date) {
    const ts = value.getTime()
    return Number.isFinite(ts) ? ts : 0
  }

  const raw = String(value).trim()
  const directTs = new Date(raw).getTime()
  if (Number.isFinite(directTs)) {
    return directTs
  }

  const normalized = raw
    .replace(/年/g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, '')
    .replace(/时/g, ':')
    .replace(/分/g, ':')
    .replace(/秒/g, '')

  const normalizedTs = new Date(normalized).getTime()
  if (Number.isFinite(normalizedTs)) {
    return normalizedTs
  }

  const matched = raw.match(
    /^(\d{4})[\/-](\d{1,2})[\/-](\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?$/
  )
  if (matched) {
    const [, year, month, day, hour = '0', minute = '0', second = '0'] = matched
    const ts = new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
      Number(second)
    ).getTime()
    return Number.isFinite(ts) ? ts : 0
  }

  return 0
}

const formatDateTime = (ts) => {
  const dateObj = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())} ${pad(dateObj.getHours())}:${pad(dateObj.getMinutes())}:${pad(dateObj.getSeconds())}`
}

const normalizeDeadlineForPicker = (value) => {
  const ts = parseTime(value)
  if (!ts) return ''
  return formatDateTime(ts)
}

const isExpired = (deadline) => {
  const ts = parseTime(deadline)
  return ts > 0 && ts < Date.now()
}

const hasScore = (row) => row.score !== null && row.score !== undefined && row.score !== ''

const isLateSubmission = (row) => {
  const submitTs = parseTime(row.submit_time)
  const deadlineTs = parseTime(row.homework_deadline)
  if (!submitTs || !deadlineTs) return false
  return submitTs > deadlineTs
}

const buildUploadUrl = (filePath) => {
  if (!filePath) return '#'
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
  if (!url || url === '#') {
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

const rebuildSubmissionStatMap = () => {
  const statMap = {}
  for (const row of submissionTableData.value) {
    const key = Number(row.homework_id)
    if (!statMap[key]) {
      statMap[key] = { submitted: 0, graded: 0 }
    }
    statMap[key].submitted += 1
    if (hasScore(row)) {
      statMap[key].graded += 1
    }
  }
  submissionStatMap.value = statMap
}

const getSubmissionStatText = (homeworkId) => {
  const stat = submissionStatMap.value[Number(homeworkId)] || { submitted: 0, graded: 0 }
  const total = teacherStudentCount.value || 0
  if (!total) return `${stat.submitted} 人提交`
  return `${stat.submitted}/${total} 已提交，已评分 ${stat.graded}`
}

const validateDeadlineFuture = (deadlineValue) => {
  const ts = parseTime(deadlineValue)
  if (!ts) {
    ElMessage.warning('请选择有效的截止时间')
    return false
  }
  if (ts <= Date.now()) {
    ElMessage.warning('截止时间必须晚于当前时间')
    return false
  }
  return true
}

const resetPublishForm = () => {
  form.title = ''
  form.content = ''
  form.deadline = ''
  homeworkFile.value = null
  homeworkFileList.value = []
  formRef.value?.clearValidate?.()
}

const onHomeworkFileChange = (file, fileList) => {
  homeworkFile.value = file?.raw || null
  homeworkFileList.value = fileList.slice(-1)
}

const onHomeworkFileRemove = () => {
  homeworkFile.value = null
  homeworkFileList.value = []
}

const loadTeacherStudents = async () => {
  const res = await getTeacherStudentList()
  teacherStudentCount.value = (res.data || []).length
}

const loadHomeworkData = async () => {
  try {
    listLoading.value = true
    const res = await getTeacherHomeworkListApi()
    tableData.value = res.data || []
    homeworkPage.value = 1
  } finally {
    listLoading.value = false
  }
}

const loadSubmissionData = async () => {
  try {
    submissionLoading.value = true
    const res = await getTeacherHomeworkSubmissionListApi()
    submissionTableData.value = res.data || []
    submissionPage.value = 1
    rebuildSubmissionStatMap()
  } finally {
    submissionLoading.value = false
  }
}

const loadData = async () => {
  await Promise.all([loadHomeworkData(), loadSubmissionData(), loadTeacherStudents()])
}

const handleHomeworkPageChange = (page) => {
  homeworkPage.value = page
}

const handleSubmissionPageChange = (page) => {
  submissionPage.value = page
}

const handlePublish = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!validateDeadlineFuture(form.deadline)) return

    try {
      loading.value = true
      const payload = new FormData()
      payload.append('title', form.title)
      payload.append('content', form.content)
      payload.append('deadline', form.deadline)
      if (homeworkFile.value) {
        payload.append('file', homeworkFile.value)
      }
      await publishHomeworkApi(payload)
      ElMessage.success('作业发布成功')
      resetPublishForm()
      await loadData()
    } finally {
      loading.value = false
    }
  })
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.title = row.title
  editForm.content = row.content
  editForm.deadline = normalizeDeadlineForPicker(row.deadline)
  editForm.file_path = row.file_path || ''
  editForm.clear_file = false
  editHomeworkFile.value = null
  editHomeworkFileList.value = []
  dialogVisible.value = true
}

const onEditHomeworkFileChange = (file, fileList) => {
  editHomeworkFile.value = file?.raw || null
  editHomeworkFileList.value = fileList.slice(-1)
}

const onEditHomeworkFileRemove = () => {
  editHomeworkFile.value = null
  editHomeworkFileList.value = []
}

const handleUpdate = async () => {
  if (!editForm.title.trim()) {
    ElMessage.warning('请填写作业标题')
    return
  }
  if (!validateDeadlineFuture(editForm.deadline)) return

  try {
    updateLoading.value = true
    const payload = new FormData()
    payload.append('title', editForm.title)
    payload.append('content', editForm.content || '')
    payload.append('deadline', editForm.deadline)
    if (editForm.clear_file) {
      payload.append('clear_file', '1')
    }
    if (editHomeworkFile.value) {
      payload.append('file', editHomeworkFile.value)
    }
    await updateTeacherHomeworkApi(editForm.id, payload)
    ElMessage.success('编辑保存成功')
    dialogVisible.value = false
    await loadData()
  } finally {
    updateLoading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除作业：${row.title}？`, '提示', { type: 'warning' })
  await deleteTeacherHomeworkApi(row.id)
  ElMessage.success('删除成功')
  await loadData()
}

const openReview = (row) => {
  reviewForm.id = row.id
  reviewForm.homework_title = row.homework_title
  reviewForm.student_username = row.student_username
  reviewForm.score = row.score ?? 0
  reviewForm.feedback = row.feedback || ''
  reviewDialogVisible.value = true
}

const handleReview = async () => {
  try {
    reviewLoading.value = true
    await reviewTeacherHomeworkSubmissionApi(reviewForm.id, {
      score: reviewForm.score,
      feedback: reviewForm.feedback
    })
    ElMessage.success('评分保存成功')
    reviewDialogVisible.value = false
    await loadSubmissionData()
  } finally {
    reviewLoading.value = false
  }
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

.board-card {
  min-height: 350px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.overview-item {
  border-radius: 10px;
  border: 1px solid #e7edf7;
  padding: 14px;
  background: linear-gradient(135deg, #f8fbff 0%, #f2f7ff 100%);
}

.board-splitter {
  height: 1px;
  margin: 14px 0;
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.12), rgba(64, 158, 255, 0.45), rgba(64, 158, 255, 0.12));
}

.teacher-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-item {
  border-radius: 10px;
  border: 1px solid #ebeef5;
  padding: 14px;
  background: #fafcff;
}

.summary-label {
  color: #909399;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.file-link {
  color: #409eff;
  text-decoration: none;
}

.file-link:hover {
  text-decoration: underline;
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

@media (max-width: 991px) {
  .board-card {
    min-height: auto;
  }

  .overview-grid,
  .teacher-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
