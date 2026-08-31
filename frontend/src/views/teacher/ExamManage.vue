<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card class="page-card">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">考试管理</div>
              <el-space :size="8">
                <el-button @click="openRetakeRequestDialog">重考申请</el-button>
                <el-button type="primary" @click="openCreateDialog">新建考试</el-button>
              </el-space>
            </div>
          </template>

          <div class="toolbar-wrap mb12">
            <el-input
              v-model.trim="examFilter.keyword"
              placeholder="搜索考试标题"
              clearable
              style="width: 240px"
            />
            <el-select v-model="examFilter.status" style="width: 130px">
              <el-option label="全部状态" value="all" />
              <el-option label="待开始" value="not_started" />
              <el-option label="进行中" value="ongoing" />
              <el-option label="已结束" value="ended" />
            </el-select>
            <el-button @click="resetExamFilter">重置</el-button>
          </div>

          <el-table
            class="page-table"
            :data="filteredExamList"
            border
            stripe
            table-layout="auto"
            highlight-current-row
            :current-row-key="currentExam?.id"
            row-key="id"
            v-loading="examLoading"
            @row-click="selectExam"
          >
            <el-table-column prop="title" label="考试标题" min-width="160" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusTypeMap[resolveExamLifecycleStatus(row)] || 'info'">{{ statusLabelMap[resolveExamLifecycleStatus(row)] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" min-width="150" />
            <el-table-column prop="end_time" label="截止时间" min-width="150" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-space :size="6">
                  <el-button link type="primary" @click.stop="openExamDetailDialog(row)">查看详情</el-button>
                  <el-button link type="danger" @click.stop="deleteExam(row)">删除</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!examLoading && filteredExamList.length === 0" description="暂无考试" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="page-card" v-if="currentExam">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">作答记录</div>
              <el-tag type="success">作答记录 {{ currentExam.submit_count || 0 }} / 学员 {{ currentExam.student_count || currentExam.submit_count || 0 }}</el-tag>
            </div>
          </template>

          <div class="exam-summary mb12">
            <div class="summary-title">{{ currentExam.title }}</div>
            <div class="summary-meta">开始时间：{{ currentExam.start_time }} | 截止时间：{{ currentExam.end_time }}</div>
            <div class="summary-meta">题目数量：{{ currentExam.question_count || 0 }} | 时长：{{ currentExam.duration_minutes }} 分钟</div>
            <div v-if="currentExam.description" class="summary-description">{{ currentExam.description }}</div>
          </div>

          <div class="toolbar-wrap mb12">
            <el-input
              v-model.trim="recordFilter.keyword"
              placeholder="搜索学员账号"
              clearable
              style="width: 220px"
            />
            <el-select v-model="recordFilter.status" style="width: 130px">
              <el-option label="全部状态" value="all" />
              <el-option label="待评分" value="pending" />
              <el-option label="已评分" value="graded" />
            </el-select>
            <el-button @click="resetRecordFilter">重置</el-button>
          </div>

          <el-table class="page-table" :data="filteredRecordList" border stripe table-layout="auto" v-loading="recordLoading">
            <el-table-column prop="student_username" label="学员" min-width="120" />
            <el-table-column prop="auto_score" label="自动分" width="90" />
            <el-table-column prop="manual_score" label="人工分" width="90" />
            <el-table-column prop="total_score" label="总分" width="90" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                {{ recordStatusLabelMap[row.status] || row.status }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-space :size="6">
                  <el-button link type="primary" @click="openGradeDialog(row)">评分</el-button>
                  <el-button link type="warning" @click="approveRetake(row)">同意重考</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recordLoading && filteredRecordList.length === 0" description="暂无作答记录" />
        </el-card>

        <el-card class="page-card" v-else>
          <el-empty description="请先选择一个考试" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="createDialogVisible" title="新建考试" width="900px" class="create-exam-dialog" top="4vh">
      <el-form :model="examForm" label-width="100px">
        <el-form-item label="考试标题">
          <el-input v-model="examForm.title" />
        </el-form-item>
        <el-form-item label="考试说明">
          <el-input v-model="examForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="开始时间">
              <el-date-picker v-model="examForm.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束时间">
              <el-date-picker v-model="examForm.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时长(分钟)">
              <el-input-number v-model="examForm.duration_minutes" :min="10" :max="600" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div class="header-wrap mb12">
        <div class="card-title">题目列表</div>
        <div class="template-actions">
          <el-select
            v-model="selectedTemplateCourse"
            placeholder="选择课程"
            style="width: 180px"
            :disabled="templateCourseOptions.length <= 1"
            @change="handleCourseChange"
          >
            <el-option v-for="item in templateCourseOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-tag v-if="fixedTeacherCourse" type="success">固定课程：{{ fixedTeacherCourse }}</el-tag>
          <el-select v-model="selectedSectionNo" placeholder="选择章节" style="width: 220px" :disabled="!selectedTemplateCourse" @change="handleSectionChange">
            <el-option
              v-for="item in sectionOptions"
              :key="item.section_no"
              :label="`第${item.section_no}节 ${item.section_title}`"
              :value="item.section_no"
            />
          </el-select>
          <template v-for="item in generationTypeOptions" :key="item.value">
            <el-input-number v-model="generationForm[item.value]" :min="0" :max="item.max" />
            <span class="count-label">{{ item.label }}</span>
          </template>
          <span class="rule-tip">{{ currentCourseRuleText }}</span>
          <el-button @click="generateQuestionsFromBank">随机生成</el-button>
          <el-button @click="addQuestion">添加题目</el-button>
        </div>
      </div>

      <div v-for="(q, idx) in questionForms" :key="idx" class="question-block">
        <el-row :gutter="10">
          <el-col :span="8">
            <el-select v-model="q.question_type" style="width: 100%">
              <el-option v-for="item in allowedManualQuestionTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <div class="fixed-score">固定分值：{{ resolveFixedScore(q.question_type) }} 分</div>
          </el-col>
        </el-row>
        <el-input v-model="q.content" class="mt8" type="textarea" :rows="2" placeholder="请输入题干" />
        <el-input
          v-if="['single', 'multi', 'pair'].includes(q.question_type)"
          v-model="q.optionsText"
          class="mt8"
          type="textarea"
          :rows="3"
          placeholder="每行一个选项，例如：A. 肾上腺素"
        />
        <el-input
          v-model="q.correct_answer"
          class="mt8"
          :placeholder="q.question_type === 'judge' ? '标准答案请输入：正确 或 错误' : '标准答案（主观题可填参考要点）'"
        />
        <el-input v-model="q.analysis" class="mt8" type="textarea" :rows="2" placeholder="题目解析" />
      </div>

      <template #footer>
        <div class="dialog-footer-sticky">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitExam">创建</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="gradeDialogVisible" title="人工评分" width="860px">
      <div v-if="gradeRecordMeta" class="mb12">
        学员：{{ gradeRecordMeta.student_username }}，自动分：{{ gradeRecordMeta.auto_score }}，当前总分：{{ gradeRecordMeta.total_score }}
      </div>
      <el-table class="page-table" :data="gradeAnswers" border stripe table-layout="auto" v-loading="gradeLoading">
        <el-table-column prop="content" label="题目" min-width="240" />
        <el-table-column label="题型" width="90">
          <template #default="{ row }">{{ formatQuestionType(row.question_type) }}</template>
        </el-table-column>
        <el-table-column prop="correct_answer" label="标准答案" min-width="140" />
        <el-table-column prop="answer_text" label="学员答案" min-width="180" />
        <el-table-column prop="analysis" label="解析" min-width="220" />
        <el-table-column prop="question_score" label="满分" width="70" />
        <el-table-column label="评分" width="120">
          <template #default="{ row }">
            <el-input-number
              v-if="['short', 'essay', 'term'].includes(row.question_type)"
              v-model="row.score_awarded"
              :min="0"
              :max="Number(row.question_score || 0)"
              :step="0.5"
            />
            <span v-else>{{ row.score_awarded }}</span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="gradeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="submitManualGrade">提交评分</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="examDetailDialogVisible" title="考试详情" width="960px">
      <div v-if="examDetail.exam" class="mb12 exam-detail-head">
        <div class="summary-title">{{ examDetail.exam.title }}</div>
        <div class="summary-meta">状态：{{ statusLabelMap[resolveExamLifecycleStatus(examDetail.exam)] || examDetail.exam.status }} | 题目数量：{{ examDetail.exam.question_count || 0 }} | 作答记录：{{ examDetail.exam.submit_count || 0 }} | 学员人数：{{ examDetail.exam.student_count || examDetail.exam.submit_count || 0 }}</div>
        <div class="summary-meta">开始时间：{{ examDetail.exam.start_time }} | 截止时间：{{ examDetail.exam.end_time }} | 时长：{{ examDetail.exam.duration_minutes }} 分钟</div>
        <div v-if="examDetail.exam.description" class="summary-description">{{ examDetail.exam.description }}</div>
      </div>

      <el-table class="page-table" :data="examDetail.questions" border stripe table-layout="auto">
        <el-table-column label="序号" width="70">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>
        <el-table-column label="题型" width="90">
          <template #default="{ row }">{{ formatQuestionType(row.question_type) }}</template>
        </el-table-column>
        <el-table-column prop="content" label="题目" min-width="260" />
        <el-table-column prop="correct_answer" label="标准答案" min-width="140" />
        <el-table-column prop="analysis" label="解析" min-width="220" />
        <el-table-column prop="score" label="分值" width="70" />
      </el-table>

      <template #footer>
        <el-button @click="examDetailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="retakeRequestDialogVisible" title="重考申请" width="960px">
      <div class="toolbar-wrap mb12">
        <el-select v-model="retakeRequestFilter.status" style="width: 140px" @change="loadRetakeRequests">
          <el-option label="全部" value="all" />
          <el-option label="待审核" value="pending" />
          <el-option label="已同意" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button @click="loadRetakeRequests">刷新</el-button>
      </div>

      <el-table :data="retakeRequestList" border stripe table-layout="auto" v-loading="retakeRequestLoading">
        <el-table-column prop="exam_title" label="考试" min-width="180" />
        <el-table-column prop="student_username" label="学员" width="120" />
        <el-table-column prop="reason" label="申请理由" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">{{ retakeStatusLabelMap[row.status] || row.status }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="申请时间" min-width="150" />
        <el-table-column prop="review_comment" label="审核意见" min-width="170" show-overflow-tooltip />
        <el-table-column label="操作" width="170">
          <template #default="{ row }">
            <el-space v-if="row.status === 'pending'" :size="6">
              <el-button link type="success" @click="reviewRetakeRequest(row, 'approve')">同意</el-button>
              <el-button link type="danger" @click="reviewRetakeRequest(row, 'reject')">拒绝</el-button>
            </el-space>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="retakeRequestDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createTeacherExamApi,
  deleteTeacherExamApi,
  generateTeacherExamQuestionsApi,
  getTeacherExamDetailApi,
  getTeacherExamListApi,
  getTeacherExamQuestionBankMetaApi,
  getTeacherExamRecordDetailApi,
  getTeacherExamRecordListApi,
  manualGradeTeacherExamRecordApi,
  approveRetakeTeacherExamRecordApi,
  getTeacherExamRetakeRequestListApi,
  reviewTeacherExamRetakeRequestApi
} from '../../api/teacher'

const examLoading = ref(false)
const recordLoading = ref(false)
const gradeLoading = ref(false)
const retakeRequestLoading = ref(false)

const examList = ref([])
const recordList = ref([])
const currentExam = ref(null)
const examFilter = reactive({
  keyword: '',
  status: 'all'
})
const recordFilter = reactive({
  keyword: '',
  status: 'all'
})

const createDialogVisible = ref(false)
const gradeDialogVisible = ref(false)
const examDetailDialogVisible = ref(false)
const retakeRequestDialogVisible = ref(false)
const selectedTemplateCourse = ref('')
const selectedSectionNo = ref(null)
const questionBankMeta = ref([])
const retakeRequestList = ref([])

const gradeRecordId = ref(null)
const gradeRecordMeta = ref(null)
const gradeAnswers = ref([])
const examDetail = reactive({
  exam: null,
  questions: []
})

const retakeRequestFilter = reactive({
  status: 'pending'
})

const generationForm = reactive({
  single: 1,
  multi: 0,
  pair: 0,
  judge: 1,
  fill: 1,
  term: 0,
  short: 0,
  essay: 0
})

const examForm = reactive({
  title: '',
  description: '',
  start_time: '',
  end_time: '',
  duration_minutes: 60
})

const questionForms = ref([])

const statusLabelMap = {
  draft: '草稿',
  published: '已发布',
  not_started: '待开始',
  ongoing: '进行中',
  ended: '已结束',
  closed: '已关闭'
}

const statusTypeMap = {
  draft: 'info',
  not_started: 'warning',
  ongoing: 'success',
  ended: 'info',
  closed: 'danger'
}

const recordStatusLabelMap = {
  pending: '待评分',
  graded: '已评分',
  submitted: '已提交',
  reviewed: '已评分'
}

const retakeStatusLabelMap = {
  pending: '待审核',
  approved: '已同意',
  rejected: '已拒绝'
}

const parseDateTime = (value) => {
  if (!value) return 0
  const normalized = String(value)
    .trim()
    .replace(/年|\//g, '-')
    .replace(/月/g, '-')
    .replace(/日/g, ' ')
    .replace(/\s+/g, ' ')
  const ts = new Date(normalized.replace(' ', 'T')).getTime()
  return Number.isFinite(ts) ? ts : 0
}

const resolveExamLifecycleStatus = (exam) => {
  const baseStatus = String(exam?.status || '')
  if (baseStatus === 'draft' || baseStatus === 'closed') return baseStatus

  const now = Date.now()
  const startTs = parseDateTime(exam?.start_time)
  const endTs = parseDateTime(exam?.end_time)

  if (startTs && now < startTs) return 'not_started'
  if (endTs && now > endTs) return 'ended'
  return 'ongoing'
}

const templateCourseOptions = computed(() => questionBankMeta.value.map((item) => item.course))
const fixedTeacherCourse = computed(() => (templateCourseOptions.value.length === 1 ? templateCourseOptions.value[0] : ''))

const filteredExamList = computed(() => {
  const keyword = examFilter.keyword.toLowerCase()
  return examList.value.filter((item) => {
    const lifecycleStatus = resolveExamLifecycleStatus(item)
    if (examFilter.status !== 'all' && lifecycleStatus !== examFilter.status) return false
    if (!keyword) return true
    return String(item.title || '').toLowerCase().includes(keyword)
  })
})

const filteredRecordList = computed(() => {
  const keyword = recordFilter.keyword.toLowerCase()
  return recordList.value.filter((item) => {
    if (recordFilter.status !== 'all' && String(item.status || '') !== recordFilter.status) return false
    if (!keyword) return true
    return String(item.student_username || '').toLowerCase().includes(keyword)
  })
})

const sectionOptions = computed(() => {
  const target = questionBankMeta.value.find((item) => item.course === selectedTemplateCourse.value)
  return target?.sections || []
})

const currentSectionMeta = computed(() => {
  return sectionOptions.value.find((item) => Number(item.section_no) === Number(selectedSectionNo.value)) || null
})

const questionTypeLabelMap = {
  single: '单选题',
  multi: '多选题',
  pair: '配伍题',
  judge: '判断题',
  fill: '填空题',
  term: '名词解释',
  short: '简答题',
  essay: '论述题'
}

const manualQuestionTypeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multi' },
  { label: '配伍题', value: 'pair' },
  { label: '判断题', value: 'judge' },
  { label: '填空题', value: 'fill' },
  { label: '名词解释', value: 'term' },
  { label: '简答题', value: 'short' },
  { label: '论述题', value: 'essay' }
]

const generationTypeOptions = computed(() => {
  const preset = courseTypePresetMap[selectedTemplateCourse.value] || {}
  const availableCounts = currentSectionMeta.value?.counts || {}
  return manualQuestionTypeOptions
    .filter((item) => Number(preset[item.value] || 0) > 0)
    .map((item) => ({
      ...item,
      max: Number(availableCounts[item.value] || 0)
    }))
})

const currentCourseRuleText = computed(() => {
  const course = selectedTemplateCourse.value
  if (!course) return '请选择课程后按对应考试结构出题'
  if (course === '西医临床' || course === '中医临床') {
    return '306/307：全选择题（单选 + 多选 + 配伍）'
  }
  if (course === '政治') {
    return '政治：选择题 + 分析题（主观题）'
  }
  if (course === '英语') {
    return '英语：客观题 + 翻译/写作（主观题）'
  }
  return '护理/口腔/公卫/基础/医技：选择 + 名词解释 + 简答 + 论述'
})

const allowedManualQuestionTypeOptions = computed(() => {
  const preset = courseTypePresetMap[selectedTemplateCourse.value] || { single: 1 }
  return manualQuestionTypeOptions.filter((item) => Number(preset[item.value] || 0) > 0)
})

const fixedScoreMap = {
  single: 5,
  multi: 2,
  pair: 2,
  judge: 4,
  fill: 6,
  term: 8,
  short: 10,
  essay: 12
}

const courseTypePresetMap = {
  西医临床: { single: 6, multi: 2, pair: 2, judge: 0, fill: 0, term: 0, short: 0, essay: 0 },
  中医临床: { single: 6, multi: 2, pair: 2, judge: 0, fill: 0, term: 0, short: 0, essay: 0 },
  口腔医学: { single: 5, multi: 2, pair: 0, judge: 0, fill: 0, term: 1, short: 1, essay: 1 },
  '其他类（护理学、医学技术、基础医学、公共卫生等）': { single: 4, multi: 2, pair: 0, judge: 0, fill: 0, term: 1, short: 2, essay: 1 },
  政治: { single: 5, multi: 3, pair: 0, judge: 0, fill: 0, term: 0, short: 2, essay: 0 },
  英语: { single: 7, multi: 0, pair: 0, judge: 0, fill: 1, term: 0, short: 2, essay: 0 }
}

const formatQuestionType = (questionType) => questionTypeLabelMap[questionType] || questionType
const resolveFixedScore = (questionType) => fixedScoreMap[questionType] || 0
const getCourseTypePreset = (course) =>
  courseTypePresetMap[course] || { single: 4, multi: 1, pair: 0, judge: 1, fill: 1, term: 0, short: 1, essay: 0 }

const resolveAvailableCount = (questionType) => {
  return Number(currentSectionMeta.value?.counts?.[questionType] || 0)
}

const capByAvailable = (questionType, wantedCount) => {
  const available = resolveAvailableCount(questionType)
  return Math.max(0, Math.min(Number(wantedCount || 0), available))
}

const applyGenerationPreset = (preset) => {
  generationForm.single = Number(preset.single || 0)
  generationForm.multi = Number(preset.multi || 0)
  generationForm.pair = Number(preset.pair || 0)
  generationForm.judge = Number(preset.judge || 0)
  generationForm.fill = Number(preset.fill || 0)
  generationForm.term = Number(preset.term || 0)
  generationForm.short = Number(preset.short || 0)
  generationForm.essay = Number(preset.essay || 0)
}

const pad2 = (value) => String(value).padStart(2, '0')

const toDateTimeString = (dateObj) => {
  return `${dateObj.getFullYear()}-${pad2(dateObj.getMonth() + 1)}-${pad2(dateObj.getDate())} ${pad2(dateObj.getHours())}:${pad2(
    dateObj.getMinutes()
  )}:${pad2(dateObj.getSeconds())}`
}

const parseDateTimeString = (value) => {
  if (!value) return null
  const normalized = String(value).replace(' ', 'T')
  const dateObj = new Date(normalized)
  if (Number.isNaN(dateObj.getTime())) {
    return null
  }
  return dateObj
}

const syncEndTimeByStartAndDuration = () => {
  const start = parseDateTimeString(examForm.start_time)
  if (!start) return
  const minutes = Number(examForm.duration_minutes || 0)
  const end = new Date(start.getTime() + minutes * 60 * 1000)
  examForm.end_time = toDateTimeString(end)
}

const initializeTimeRange = () => {
  const now = new Date()
  examForm.start_time = toDateTimeString(now)
  syncEndTimeByStartAndDuration()
}

const addQuestion = () => {
  questionForms.value.unshift({
    question_type: 'single',
    content: '',
    optionsText: '',
    correct_answer: '',
    analysis: ''
  })
}

const loadQuestionBankMeta = async () => {
  try {
    const res = await getTeacherExamQuestionBankMetaApi()
    questionBankMeta.value = res.data || []
    if (fixedTeacherCourse.value) {
      selectedTemplateCourse.value = fixedTeacherCourse.value
    }
  } catch (error) {
    questionBankMeta.value = []
  }
}

const resetGenerationCounts = () => {
  const preset = getCourseTypePreset(selectedTemplateCourse.value)
  applyGenerationPreset({
    single: capByAvailable('single', preset.single),
    multi: capByAvailable('multi', preset.multi),
    pair: capByAvailable('pair', preset.pair),
    judge: capByAvailable('judge', preset.judge),
    fill: capByAvailable('fill', preset.fill),
    term: capByAvailable('term', preset.term),
    short: capByAvailable('short', preset.short),
    essay: capByAvailable('essay', preset.essay)
  })
}

const handleCourseChange = () => {
  selectedSectionNo.value = null
  const preset = getCourseTypePreset(selectedTemplateCourse.value)
  applyGenerationPreset(preset)
}

const handleSectionChange = () => {
  resetGenerationCounts()
}

const resetExamFilter = () => {
  examFilter.keyword = ''
  examFilter.status = 'all'
}

const resetRecordFilter = () => {
  recordFilter.keyword = ''
  recordFilter.status = 'all'
}

const generateQuestionsFromBank = async () => {
  if (!selectedTemplateCourse.value || !selectedSectionNo.value) {
    ElMessage.warning('请先选择课程和章节')
    return
  }

  const payload = {
    course: selectedTemplateCourse.value,
    section_no: selectedSectionNo.value,
    auto_mix: false,
    counts: {
      single: Number(generationForm.single || 0),
      multi: Number(generationForm.multi || 0),
      pair: Number(generationForm.pair || 0),
      judge: Number(generationForm.judge || 0),
      fill: Number(generationForm.fill || 0),
      term: Number(generationForm.term || 0),
      short: Number(generationForm.short || 0),
      essay: Number(generationForm.essay || 0)
    }
  }

  const total =
    payload.counts.single +
    payload.counts.multi +
    payload.counts.pair +
    payload.counts.judge +
    payload.counts.fill +
    payload.counts.term +
    payload.counts.short +
    payload.counts.essay
  if (!total) {
    ElMessage.warning('请至少设置一种题型数量')
    return
  }

  if (currentSectionMeta.value?.counts) {
    const shortageLabels = []
    const currentCounts = currentSectionMeta.value.counts
    Object.keys(payload.counts).forEach((key) => {
      const need = Number(payload.counts[key] || 0)
      const have = Number(currentCounts[key] || 0)
      if (need > have) {
        shortageLabels.push(`${questionTypeLabelMap[key] || key}需${need}题，现有${have}题`)
      }
    })
    if (shortageLabels.length) {
      ElMessage.warning(`题库题量不足：${shortageLabels.join('；')}`)
      return
    }
  }

  try {
    const res = await generateTeacherExamQuestionsApi(payload)
    const questions = Array.isArray(res.data?.questions) ? res.data.questions : []

    const pickedCounts = {
      single: 0,
      multi: 0,
      pair: 0,
      judge: 0,
      fill: 0,
      term: 0,
      short: 0,
      essay: 0
    }
    questions.forEach((question) => {
      const key = question?.question_type
      if (Object.prototype.hasOwnProperty.call(pickedCounts, key)) {
        pickedCounts[key] += 1
      }
    })

    const mismatchType = Object.keys(payload.counts).find((key) => Number(payload.counts[key] || 0) !== Number(pickedCounts[key] || 0))
    if (mismatchType || questions.length !== total) {
      const label = questionTypeLabelMap[mismatchType] || mismatchType || '题型'
      ElMessage.error(`随机抽题结果与所选数量不一致：${label}`)
      return
    }

    examForm.title = res.data?.title || examForm.title
    examForm.description = res.data?.description || examForm.description
    syncEndTimeByStartAndDuration()
    questionForms.value = questions.map((question) => ({
      ...question,
      optionsText: (question.options || []).join('\n')
    }))
    ElMessage.success(`题目已从题库随机抽取，共 ${questions.length} 题`)
  } catch (error) {
    const message = String(error?.message || '')
    if (message.includes('题库题量不足') || message.includes('题数量不足')) {
      ElMessage.warning('题库题量不足，请先补充题目后再生成')
      return
    }
    ElMessage.error(message || '随机抽题失败，请稍后重试')
  }
}

const resetCreateForm = () => {
  examForm.title = ''
  examForm.description = ''
  examForm.duration_minutes = 60
  initializeTimeRange()
  questionForms.value = []
  addQuestion()
}

const openCreateDialog = () => {
  resetCreateForm()
  selectedTemplateCourse.value = fixedTeacherCourse.value || ''
  selectedSectionNo.value = null
  const preset = getCourseTypePreset(selectedTemplateCourse.value)
  applyGenerationPreset(preset)
  createDialogVisible.value = true
}

watch(
  () => examForm.duration_minutes,
  () => {
    if (createDialogVisible.value) {
      syncEndTimeByStartAndDuration()
    }
  }
)

watch(
  () => examForm.start_time,
  () => {
    if (createDialogVisible.value) {
      syncEndTimeByStartAndDuration()
    }
  }
)

const loadExamList = async () => {
  try {
    examLoading.value = true
    const res = await getTeacherExamListApi()
    examList.value = res.data || []
    if (examList.value.length && !currentExam.value) {
      await selectExam(examList.value[0])
    }
  } finally {
    examLoading.value = false
  }
}

const selectExam = async (exam) => {
  currentExam.value = exam
  try {
    recordLoading.value = true
    const res = await getTeacherExamRecordListApi(exam.id)
    recordList.value = res.data || []
    // 与下方记录表保持同口径，避免顶部人数显示与列表不一致
    const uniqueStudentCount = new Set(recordList.value.map((item) => item.student_id)).size
    if (currentExam.value) {
      currentExam.value.submit_count = recordList.value.length
      currentExam.value.student_count = uniqueStudentCount
    }
  } finally {
    recordLoading.value = false
  }
}

const openExamDetailDialog = async (exam) => {
  const res = await getTeacherExamDetailApi(exam.id)
  examDetail.exam = res.data?.exam || null
  examDetail.questions = res.data?.questions || []
  examDetailDialogVisible.value = true
}

const deleteExam = async (exam) => {
  await ElMessageBox.confirm(`确认删除考试《${exam.title}》？删除后题目、作答记录和评分记录将一并移除。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })

  await deleteTeacherExamApi(exam.id)
  if (currentExam.value?.id === exam.id) {
    currentExam.value = null
    recordList.value = []
  }
  if (examDetail.exam?.id === exam.id) {
    examDetailDialogVisible.value = false
    examDetail.exam = null
    examDetail.questions = []
  }
  ElMessage.success('考试已删除')
  await loadExamList()
}

const submitExam = async () => {
  if (!examForm.title || !examForm.start_time || !examForm.end_time) {
    ElMessage.warning('请完整填写考试基础信息')
    return
  }
  if (!questionForms.value.length) {
    ElMessage.warning('请至少添加一道题目')
    return
  }

  const questions = questionForms.value.map((q) => ({
    question_type: q.question_type,
    content: q.content,
    score: resolveFixedScore(q.question_type),
    correct_answer: q.correct_answer,
    analysis: q.analysis,
    options:
      ['single', 'multi', 'pair'].includes(q.question_type)
        ? q.optionsText.split('\n').map((line) => line.trim()).filter(Boolean)
        : []
  }))

  await createTeacherExamApi({ ...examForm, questions })
  ElMessage.success('考试创建成功')
  createDialogVisible.value = false
  currentExam.value = null
  await loadExamList()
}

const openGradeDialog = async (record) => {
  gradeDialogVisible.value = true
  gradeRecordId.value = record.id
  gradeRecordMeta.value = record
  try {
    gradeLoading.value = true
    const res = await getTeacherExamRecordDetailApi(record.id)
    gradeAnswers.value = (res.data?.answers || []).map((item) => ({ ...item, score_awarded: Number(item.score_awarded || 0) }))
  } finally {
    gradeLoading.value = false
  }
}

const submitManualGrade = async () => {
  if (!gradeRecordId.value) return

  const grading_items = gradeAnswers.value
    .filter((item) => ['short', 'essay', 'term'].includes(item.question_type))
    .map((item) => ({
      answer_id: item.answer_id,
      score_awarded: Number(item.score_awarded || 0)
    }))

  await manualGradeTeacherExamRecordApi(gradeRecordId.value, { grading_items })
  ElMessage.success('人工评分已保存')
  gradeDialogVisible.value = false
  if (currentExam.value) {
    await selectExam(currentExam.value)
  }
}

const approveRetake = async (record) => {
  await ElMessageBox.confirm(
    `确认同意学员 ${record.student_username} 重考？同意后将清除该学员本场考试已提交记录。`,
    '同意重考',
    {
      type: 'warning',
      confirmButtonText: '确认同意',
      cancelButtonText: '取消'
    }
  )

  await approveRetakeTeacherExamRecordApi(record.id)
  ElMessage.success('已同意重考，学员可重新作答')
  if (currentExam.value) {
    await selectExam(currentExam.value)
  }
}

const loadRetakeRequests = async () => {
  try {
    retakeRequestLoading.value = true
    const res = await getTeacherExamRetakeRequestListApi({ status: retakeRequestFilter.status })
    retakeRequestList.value = res.data || []
  } finally {
    retakeRequestLoading.value = false
  }
}

const openRetakeRequestDialog = async () => {
  retakeRequestDialogVisible.value = true
  await loadRetakeRequests()
}

const reviewRetakeRequest = async (row, action) => {
  const isApprove = action === 'approve'
  const prompt = await ElMessageBox.prompt(
    isApprove ? '请输入审核意见（可选）' : '请输入拒绝原因（可选）',
    isApprove ? '同意重考' : '拒绝重考',
    {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputValue: '',
      inputPlaceholder: isApprove ? '例如：请在截止前认真完成' : '例如：理由不充分，请补充说明',
      closeOnClickModal: false
    }
  ).catch(() => null)
  if (!prompt) return

  await reviewTeacherExamRetakeRequestApi(row.id, {
    action,
    comment: String(prompt.value || '').trim()
  })
  ElMessage.success(isApprove ? '已同意重考申请' : '已拒绝重考申请')
  await loadRetakeRequests()
  if (currentExam.value) {
    await selectExam(currentExam.value)
  }
}

onMounted(async () => {
  await Promise.allSettled([loadExamList(), loadQuestionBankMeta()])
})
</script>

<style scoped>
.question-block {
  border: 1px solid var(--line-color);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.rule-tip {
  color: var(--text-secondary);
  font-size: 12px;
  margin: 0 8px;
  white-space: nowrap;
}

.mt8 {
  margin-top: 8px;
}

.mb12 {
  margin-bottom: 12px;
}

.template-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.fixed-score {
  line-height: 32px;
  color: var(--text-secondary);
  font-size: 13px;
}

.exam-summary,
.exam-detail-head {
  padding: 12px;
  border: 1px solid var(--line-color);
  border-radius: 10px;
  background: var(--panel-muted, #fafafa);
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-strong);
}

.summary-meta {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.summary-description {
  margin-top: 8px;
  color: var(--text-primary);
  line-height: 1.6;
}

.count-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.dialog-footer-sticky {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 0 4px;
  background: var(--panel-bg, #fff);
  z-index: 20;
}

:deep(.create-exam-dialog .el-dialog__body) {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding-bottom: 12px;
}

:deep(.create-exam-dialog .el-dialog__footer) {
  position: sticky;
  bottom: 0;
  background: var(--panel-bg, #fff);
  border-top: 1px solid var(--line-color);
  z-index: 21;
}
</style>
