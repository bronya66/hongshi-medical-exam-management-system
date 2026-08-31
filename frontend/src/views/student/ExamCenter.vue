<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="24">
        <el-card class="page-card">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">考试列表</div>
              <el-button @click="loadData">刷新</el-button>
            </div>
          </template>

          <div class="toolbar-wrap">
            <el-input
              v-model.trim="filter.keyword"
              placeholder="搜索考试名称"
              clearable
              style="width: 260px"
              @input="currentPage = 1"
            />
            <el-select v-model="filter.status" style="width: 150px" @change="currentPage = 1">
              <el-option label="全部状态" value="all" />
              <el-option label="可作答" value="todo" />
              <el-option label="待评分中" value="pending" />
              <el-option label="可查看成绩" value="scored" />
            </el-select>
            <el-button @click="resetFilter">重置</el-button>
          </div>

          <el-table class="page-table" :data="pagedExamList" border stripe table-layout="auto" v-loading="loading">
            <el-table-column prop="title" label="考试" min-width="160" />
            <el-table-column label="题数" width="80">
              <template #default="{ row }">{{ row.question_count || 0 }}</template>
            </el-table-column>
            <el-table-column prop="duration_minutes" label="时长" width="90" />
            <el-table-column prop="start_time" label="开始时间" min-width="160" />
            <el-table-column prop="end_time" label="截止时间" min-width="160" />
            <el-table-column label="成绩" width="90">
              <template #default="{ row }">{{ row.record_id && Number(row.can_view_analysis) === 1 && Number(row.can_view_detail) === 1 ? row.total_score : '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="resolveExamTagType(row)">
                  {{ resolveExamTagLabel(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button v-if="!row.record_id" link type="primary" :disabled="!canTakeExam(row)" @click="openExam(row)">开始作答</el-button>
                <el-button v-else link type="primary" @click="openRecordDetail({ id: row.record_id })">
                  {{ Number(row.can_view_analysis) === 1 ? '查看成绩与解析' : '查看试卷详情' }}
                </el-button>
                <el-button
                  v-if="row.record_id && Number(row.can_request_retake) === 1"
                  link
                  type="warning"
                  @click="openRetakeRequestDialog(row)"
                >
                  申请重考
                </el-button>
                <el-tag v-else-if="row.record_id && row.retake_request_status === 'pending'" type="warning">重考待审核</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && filteredExamList.length === 0" description="暂无考试" />
          <div class="pagination-wrap" v-if="filteredExamList.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredExamList.length"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="examDialogVisible" :title="activeExam?.title || '考试作答'" width="900px">
      <div v-if="activeExam" class="mb12">考试时长：{{ activeExam.duration_minutes }} 分钟</div>
      <el-form>
        <div v-for="(q, idx) in activeQuestions" :key="q.id" class="question-block">
          <div class="question-title">{{ idx + 1 }}. {{ q.content }}（{{ q.score }}分）</div>

          <el-radio-group v-if="q.question_type === 'single'" v-model="answerMap[q.id]" class="mt8">
            <el-radio v-for="item in q.options || []" :key="item" :label="item">{{ item }}</el-radio>
          </el-radio-group>

          <el-checkbox-group v-else-if="q.question_type === 'multi'" v-model="answerMap[q.id]" class="mt8">
            <el-checkbox v-for="item in q.options || []" :key="item" :label="item">{{ item }}</el-checkbox>
          </el-checkbox-group>

          <el-radio-group v-else-if="q.question_type === 'pair'" v-model="answerMap[q.id]" class="mt8">
            <el-radio v-for="item in q.options || []" :key="item" :label="item">{{ item }}</el-radio>
          </el-radio-group>

          <el-radio-group v-else-if="q.question_type === 'judge'" v-model="answerMap[q.id]" class="mt8">
            <el-radio label="正确">正确</el-radio>
            <el-radio label="错误">错误</el-radio>
          </el-radio-group>

          <el-input
            v-else-if="q.question_type === 'fill'"
            v-model="answerMap[q.id]"
            class="mt8"
            placeholder="请输入答案"
          />

          <el-input
            v-else
            v-model="answerMap[q.id]"
            class="mt8"
            type="textarea"
            :rows="3"
            placeholder="请输入主观题作答内容"
          />
        </div>
      </el-form>

      <template #footer>
        <el-button @click="examDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExam">提交答卷</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="recordDialogVisible" title="考试记录详情" width="920px">
      <div v-if="recordDetail.record" class="mb12">
        <template v-if="Number(recordDetail.record.can_view_analysis) === 1">
          {{ recordDetail.record.exam_title }} | 自动分：{{ recordDetail.record.auto_score }} | 人工分：{{ recordDetail.record.manual_score }} | 总分：{{ recordDetail.record.total_score }}
        </template>
        <template v-else>
          {{ recordDetail.record.exam_title }} | 考试未截止，当前仅可查看我的作答详情
        </template>
      </div>

      <el-alert
        v-if="recordDetail.record && Number(recordDetail.record.can_view_analysis) !== 1"
        type="info"
        :closable="false"
        show-icon
        title="答案解析将在考试截止后开放"
        class="mb12"
      />

      <el-table class="page-table" :data="recordDetail.answers || []" border stripe table-layout="auto">
        <el-table-column prop="content" label="题目" min-width="220" />
        <el-table-column label="题型" width="90">
          <template #default="{ row }">{{ formatQuestionType(row.question_type) }}</template>
        </el-table-column>
        <el-table-column v-if="Number(recordDetail.record?.can_view_analysis) === 1" prop="correct_answer" label="标准答案" min-width="140" />
        <el-table-column prop="answer_text" label="我的答案" min-width="140" />
        <el-table-column v-if="Number(recordDetail.record?.can_view_analysis) === 1" prop="analysis" label="解析" min-width="220" />
        <el-table-column prop="score_awarded" label="得分" width="80" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="retakeDialogVisible" title="申请重考" width="520px">
      <div v-if="retakeExamRow" class="mb12">考试：{{ retakeExamRow.title }}</div>
      <el-form label-width="84px">
        <el-form-item label="申请理由">
          <el-input
            v-model.trim="retakeReason"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="请说明申请重考的原因（不少于5个字）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="retakeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRetakeRequest">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getStudentExamDetailApi,
  getStudentExamListApi,
  getStudentExamRecordDetailApi,
  submitStudentExamApi,
  submitStudentExamRetakeRequestApi
} from '../../api/student'

const loading = ref(false)
const examDialogVisible = ref(false)
const recordDialogVisible = ref(false)
const retakeDialogVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const examList = ref([])
const activeExam = ref(null)
const activeQuestions = ref([])
const answerMap = reactive({})
const retakeExamRow = ref(null)
const retakeReason = ref('')
const filter = reactive({
  keyword: '',
  status: 'all'
})

const recordDetail = reactive({
  record: null,
  answers: []
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

const formatQuestionType = (questionType) => questionTypeLabelMap[questionType] || questionType

const parseDateTime = (value) => {
  if (!value) return 0
  const ts = new Date(String(value).replace(' ', 'T')).getTime()
  return Number.isFinite(ts) ? ts : 0
}

const canTakeExam = (item) => {
  if (item?.record_id) return false
  if (Object.prototype.hasOwnProperty.call(item || {}, 'can_take_exam')) {
    return Number(item.can_take_exam) === 1
  }
  const now = Date.now()
  const startTs = parseDateTime(item?.start_time)
  const endTs = parseDateTime(item?.end_time)
  if (startTs && now < startTs) return false
  if (endTs && now > endTs) return false
  return true
}

const resolveExamTagLabel = (item) => {
  if (item?.retake_request_status === 'pending') return '重考待审核'
  if (!item?.record_id) {
    const phase = String(item?.exam_phase || '')
    if (phase === 'not_started') return '未开始'
    if (phase === 'ended') return '已截止'
    if (phase === 'ongoing') return '可作答'

    const now = Date.now()
    const startTs = parseDateTime(item?.start_time)
    const endTs = parseDateTime(item?.end_time)
    if (startTs && now < startTs) return '未开始'
    if (endTs && now > endTs) return '已截止'
    return '可作答'
  }
  return Number(item.can_view_analysis) === 1 ? '可查看成绩' : '已提交'
}

const resolveExamTagType = (item) => {
  if (item?.retake_request_status === 'pending') return 'warning'
  if (!item?.record_id) {
    const label = resolveExamTagLabel(item)
    if (label === '已截止') return 'danger'
    if (label === '未开始') return 'warning'
    return 'info'
  }
  return Number(item.can_view_analysis) === 1 ? 'success' : 'info'
}

const normalizeExamStatus = (item) => {
  if (!item.record_id) return canTakeExam(item) ? 'todo' : 'locked'
  if (item?.retake_request_status === 'pending') return 'pending'
  return Number(item.can_view_analysis) === 1 ? 'scored' : 'pending'
}

const filteredExamList = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  return examList.value.filter((item) => {
    const status = normalizeExamStatus(item)
    if (filter.status !== 'all' && status !== filter.status) return false
    if (!keyword) return true
    return String(item.title || '').toLowerCase().includes(keyword)
  })
})

const pagedExamList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredExamList.value.slice(start, start + pageSize.value)
})

const loadData = async () => {
  try {
    loading.value = true
    const examRes = await getStudentExamListApi()
    examList.value = examRes.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetFilter = () => {
  filter.keyword = ''
  filter.status = 'all'
  currentPage.value = 1
}

const openExam = async (exam) => {
  if (!canTakeExam(exam)) {
    const label = resolveExamTagLabel(exam)
    ElMessage.warning(label === '未开始' ? '考试未开始，暂不能作答' : '考试已截止，不能参加')
    return
  }
  const res = await getStudentExamDetailApi(exam.id)
  activeExam.value = res.data?.exam || exam
  activeQuestions.value = res.data?.questions || []

  Object.keys(answerMap).forEach((key) => {
    delete answerMap[key]
  })
  activeQuestions.value.forEach((q) => {
    answerMap[q.id] = q.question_type === 'multi' ? [] : ''
  })

  examDialogVisible.value = true
}

const submitExam = async () => {
  if (!activeExam.value) return

  const hasUnfinished = activeQuestions.value.some((q) => {
    if (q.question_type === 'multi') {
      return !Array.isArray(answerMap[q.id]) || answerMap[q.id].length === 0
    }
    return !String(answerMap[q.id] || '').trim()
  })
  if (hasUnfinished) {
    await ElMessageBox.confirm('存在未作答题目，是否仍然提交？', '提示', { type: 'warning' })
  }

  const answers = activeQuestions.value.map((q) => ({
    question_id: q.id,
    answer_text: q.question_type === 'multi' ? (Array.isArray(answerMap[q.id]) ? answerMap[q.id].join(';') : '') : answerMap[q.id]
  }))

  const res = await submitStudentExamApi({
    exam_id: activeExam.value.id,
    answers
  })

  ElMessage.success(`提交成功，自动判分：${res.data?.auto_score ?? 0}`)
  examDialogVisible.value = false
  await loadData()
  if (res.data?.record_id && Number(res.data?.can_view_detail) === 1) {
    await openRecordDetail({ id: res.data.record_id })
  } else if (res.data?.record_id) {
    ElMessage.info(res.data?.pending_message || '已提交，等待老师评分后可查看成绩与详情')
  }
}

const openRecordDetail = async (record) => {
  const res = await getStudentExamRecordDetailApi(record.id)
  recordDetail.record = res.data?.record || null
  recordDetail.answers = res.data?.answers || []
  recordDialogVisible.value = true
}

const openRetakeRequestDialog = (row) => {
  retakeExamRow.value = row
  retakeReason.value = ''
  retakeDialogVisible.value = true
}

const submitRetakeRequest = async () => {
  if (!retakeExamRow.value?.id) return
  if (String(retakeReason.value || '').trim().length < 5) {
    ElMessage.warning('申请理由至少 5 个字')
    return
  }

  await submitStudentExamRetakeRequestApi({
    exam_id: retakeExamRow.value.id,
    reason: retakeReason.value
  })
  ElMessage.success('重考申请已提交，请等待老师审核')
  retakeDialogVisible.value = false
  await loadData()
}

loadData()
</script>

<style scoped>
.question-block {
  border: 1px solid var(--line-color);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.question-title {
  font-weight: 600;
  color: var(--text-strong);
}

.mt8 {
  margin-top: 8px;
}

.mb12 {
  margin-bottom: 12px;
}

.toolbar-wrap {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
