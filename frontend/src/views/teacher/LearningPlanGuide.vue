<template>
  <div class="page-shell">
    <el-row :gutter="16" class="mb12">
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="指导学员" :value="summary.studentTotal" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="计划总数" :value="summary.planTotal" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="任务完成率" :value="summary.completionRate" suffix="%" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="已完成任务时长(分钟)" :value="summary.totalMinutes" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="11">
        <el-card class="page-card">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">学员计划概览</div>
              <el-button type="primary" @click="openImport()">新增学习计划</el-button>
            </div>
          </template>

          <el-form :inline="true" class="mb12">
            <el-form-item label="关键词">
              <el-input v-model.trim="filter.keyword" placeholder="姓名或账号" style="width: 180px" @input="currentPage = 1" />
            </el-form-item>
            <el-form-item label="风险筛选">
              <el-select v-model="filter.risk" style="width: 150px" @change="currentPage = 1">
                <el-option label="全部" value="all" />
                <el-option label="待跟进" value="risk" />
                <el-option label="进展良好" value="good" />
              </el-select>
            </el-form-item>
          </el-form>

          <el-table
            class="page-table"
            :data="pagedTableData"
            border
            stripe
            table-layout="auto"
            row-key="student_id"
            highlight-current-row
            v-loading="loading"
            @row-click="handleOverviewRowClick"
          >
            <el-table-column prop="student_name" label="学员" min-width="140" />
            <el-table-column prop="student_username" label="账号" min-width="130" />
            <el-table-column prop="plan_count" label="计划" width="70" />
            <el-table-column label="完成率" width="110">
              <template #default="{ row }">
                <span>{{ calcCompletionRate(row.done_task_count, row.task_count) }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="studentRiskType(row)">{{ studentRiskLabel(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="viewDetail(row)">详情</el-button>
                <el-button link type="success" @click.stop="openImport(row)">新增计划</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无学员数据" />
          <div class="pagination-wrap" v-if="filteredTableData.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredTableData.length"
              @current-change="(p) => (currentPage = p)"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="13">
        <el-card class="page-card" v-if="selectedStudent">
          <template #header>
            <div class="header-wrap">
              <div>
                <div class="card-title">{{ selectedStudent.student_name }} 的学习计划详情</div>
                <div class="sub-text">账号：{{ selectedStudent.student_username }}</div>
              </div>
              <el-space>
                <el-button type="primary" @click="openTaskCreate">新增任务</el-button>
                <el-button plain @click="viewDetail(selectedStudent)">刷新</el-button>
              </el-space>
            </div>
          </template>

          <div class="detail-summary-grid">
            <div class="summary-box">
              <div class="summary-label">计划数</div>
              <div class="summary-value">{{ detail.summary.plan_count || 0 }}</div>
            </div>
            <div class="summary-box">
              <div class="summary-label">任务完成率</div>
              <div class="summary-value">{{ detail.summary.completion_rate || 0 }}%</div>
            </div>
            <div class="summary-box">
              <div class="summary-label">已完成任务时长</div>
              <div class="summary-value">{{ detail.summary.total_minutes || 0 }} 分钟</div>
            </div>
            <div class="summary-box">
              <div class="summary-label">任务总量</div>
              <div class="summary-value">{{ detail.summary.task_done || 0 }}/{{ detail.summary.task_total || 0 }}</div>
            </div>
          </div>

          <el-divider content-position="left">学习计划</el-divider>
          <el-table class="page-table" :data="pagedDetailPlans" size="small" border stripe max-height="210" table-layout="auto" v-loading="detailLoading">
            <el-table-column prop="title" label="计划标题" min-width="170" />
            <el-table-column label="周期" min-width="160">
              <template #default="{ row }">{{ formatDisplayDate(row.start_date) }} ~ {{ formatDisplayDate(row.end_date) }}</template>
            </el-table-column>
            <el-table-column label="完成" width="90">
              <template #default="{ row }">{{ row.task_done || 0 }}/{{ row.task_total || 0 }}</template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap" v-if="detail.plans.length > detailPlanPageSize">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="detailPlanPage"
              :page-size="detailPlanPageSize"
              :total="detail.plans.length"
              @current-change="(p) => (detailPlanPage = p)"
            />
          </div>

          <el-divider content-position="left">近期待办任务</el-divider>
          <el-table class="page-table" :data="pagedDetailTasks" size="small" border stripe max-height="210" table-layout="auto" v-loading="detailLoading">
            <el-table-column prop="plan_title" label="所属计划" min-width="120" show-overflow-tooltip />
            <el-table-column prop="task_title" label="任务" min-width="180" show-overflow-tooltip />
            <el-table-column label="日期" width="110">
              <template #default="{ row }">{{ formatDisplayDate(row.task_date) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_done ? 'success' : 'warning'">{{ row.is_done ? '已完成' : '待完成' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap" v-if="detail.tasks.length > detailTaskPageSize">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="detailTaskPage"
              :page-size="detailTaskPageSize"
              :total="detail.tasks.length"
              @current-change="(p) => (detailTaskPage = p)"
            />
          </div>

          <el-divider content-position="left">学习感悟（进度备注）</el-divider>
          <el-table class="page-table" :data="pagedDetailProgress" size="small" border stripe max-height="220" table-layout="auto" v-loading="detailLoading">
            <el-table-column label="日期" width="120">
              <template #default="{ row }">{{ formatDisplayDate(row.progress_date) }}</template>
            </el-table-column>
            <el-table-column prop="plan_title" label="所属计划" min-width="150" show-overflow-tooltip />
            <el-table-column prop="study_minutes" label="学习时长(分钟)" width="130" />
            <el-table-column prop="note" label="学习感悟" min-width="220" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.note || '-' }}
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap" v-if="detail.progress.length > detailProgressPageSize">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="detailProgressPage"
              :page-size="detailProgressPageSize"
              :total="detail.progress.length"
              @current-change="(p) => (detailProgressPage = p)"
            />
          </div>

        </el-card>

        <el-card class="page-card" v-else>
          <el-empty description="请选择左侧学员查看学习指导详情" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="新增学习计划" width="720px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择学员">
          <el-select v-model="form.student_ids" multiple filterable collapse-tags style="width: 100%" placeholder="请选择学员">
            <el-option v-for="item in tableData" :key="item.student_id" :label="`${item.student_name}（${item.student_username}）`" :value="item.student_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划标题">
          <el-input v-model="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="计划目标">
          <el-input v-model="form.target" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="初始任务">
          <el-input
            v-model="taskTemplateText"
            type="textarea"
            :rows="7"
            :placeholder="taskTemplatePlaceholder"
          />
          <div class="sub-text">当前指导课程：{{ teacherCourse || '未绑定' }}。保存时会自动忽略空行，日期格式必须是 YYYY-MM-DD。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport">保存计划</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="taskDialogVisible" title="老师新增学习任务" width="600px">
      <el-form :model="taskForm" label-width="110px">
        <el-form-item label="所属计划">
          <el-select v-model="taskForm.plan_id" style="width: 100%" placeholder="请选择计划">
            <el-option v-for="item in detail.plans" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务标题">
          <el-input v-model.trim="taskForm.task_title" maxlength="160" show-word-limit placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务日期">
          <el-date-picker v-model="taskForm.task_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="预计时长(分钟)">
          <el-input-number v-model="taskForm.estimated_minutes" :min="0" :max="1440" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTaskCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createTeacherLearningTaskApi,
  getTeacherLearningPlanOverviewApi,
  getTeacherStudentLearningPlanDetailApi,
  importTeacherLearningPlanTemplateApi
} from '../../api/teacher'

const loading = ref(false)
const detailLoading = ref(false)
const dialogVisible = ref(false)
const tableData = ref([])
const teacherCourse = ref('')
const selectedStudent = ref(null)
const taskTemplateText = ref('')
const currentPage = ref(1)
const pageSize = ref(8)
const taskDialogVisible = ref(false)
const detailPlanPage = ref(1)
const detailTaskPage = ref(1)
const detailProgressPage = ref(1)
const detailPlanPageSize = 5
const detailTaskPageSize = 6
const detailProgressPageSize = 6

const detail = reactive({
  summary: { plan_count: 0, task_total: 0, task_done: 0, total_minutes: 0, completion_rate: 0 },
  plans: [],
  tasks: [],
  progress: []
})

const form = reactive({
  student_ids: [],
  title: '',
  target: '',
  start_date: '',
  end_date: ''
})

const taskForm = reactive({
  plan_id: null,
  task_title: '',
  task_date: '',
  estimated_minutes: 60
})

const filter = reactive({
  keyword: '',
  risk: 'all'
})

const calcCompletionRate = (done, total) => {
  const totalNum = Number(total || 0)
  if (!totalNum) return 0
  return Number(((Number(done || 0) / totalNum) * 100).toFixed(1))
}

const studentRiskLabel = (row) => {
  const planCount = Number(row.plan_count || 0)
  const taskCount = Number(row.task_count || 0)
  if (!planCount) return '待跟进'
  const rate = calcCompletionRate(row.done_task_count, taskCount)
  if (rate < 60) return '待跟进'
  return '进展良好'
}

const studentRiskType = (row) => {
  const label = studentRiskLabel(row)
  if (label === '待跟进') return 'danger'
  return 'success'
}

const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    if (filter.risk === 'risk' && studentRiskLabel(item) !== '待跟进') return false
    if (filter.risk === 'good' && studentRiskLabel(item) !== '进展良好') return false
    if (!keyword) return true
    return String(item.student_name || '').toLowerCase().includes(keyword) || String(item.student_username || '').toLowerCase().includes(keyword)
  })
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const summary = computed(() => {
  const studentTotal = tableData.value.length
  const planTotal = tableData.value.reduce((sum, item) => sum + Number(item.plan_count || 0), 0)
  const taskTotal = tableData.value.reduce((sum, item) => sum + Number(item.task_count || 0), 0)
  const doneTotal = tableData.value.reduce((sum, item) => sum + Number(item.done_task_count || 0), 0)
  const totalMinutes = tableData.value.reduce((sum, item) => sum + Number(item.total_minutes || 0), 0)
  const completionRate = taskTotal ? Number(((doneTotal / taskTotal) * 100).toFixed(1)) : 0
  return {
    studentTotal,
    planTotal,
    completionRate,
    totalMinutes
  }
})

const pagedDetailPlans = computed(() => {
  const start = (detailPlanPage.value - 1) * detailPlanPageSize
  return detail.plans.slice(start, start + detailPlanPageSize)
})

const pagedDetailTasks = computed(() => {
  const start = (detailTaskPage.value - 1) * detailTaskPageSize
  return detail.tasks.slice(start, start + detailTaskPageSize)
})

const pagedDetailProgress = computed(() => {
  const start = (detailProgressPage.value - 1) * detailProgressPageSize
  return detail.progress.slice(start, start + detailProgressPageSize)
})

const taskTemplatePlaceholder = computed(() => {
  const course = teacherCourse.value || ''
  let demoTask = '病例分析训练|2026-03-20|60'

  if (course === '英语') {
    demoTask = '阅读与翻译训练|2026-03-20|60'
  } else if (course === '政治') {
    demoTask = '时政与主观题框架复盘|2026-03-20|60'
  } else if (course === '中医临床') {
    demoTask = '辨证论治思路整理|2026-03-20|60'
  } else if (course === '口腔医学') {
    demoTask = '口腔修复病例要点复盘|2026-03-20|60'
  } else if (course === '其他类（护理学、医学技术、基础医学、公共卫生等）') {
    demoTask = '核心知识点专题训练|2026-03-20|60'
  }

  return `每行一个任务，支持两种格式：\n1) 只写标题：背诵解剖学重点\n2) 标题|日期|分钟：${demoTask}`
})

const formatDisplayDate = (value) => {
  if (!value) return '-'
  const text = String(value).trim()
  if (!text) return '-'
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
  const chineseDateMatch = text.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日$/)
  if (chineseDateMatch) {
    const [, y, m, d] = chineseDateMatch
    return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  }
  return text
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getTeacherLearningPlanOverviewApi()
    if (Array.isArray(res.data)) {
      tableData.value = res.data
      teacherCourse.value = ''
    } else {
      tableData.value = res.data?.students || []
      teacherCourse.value = res.data?.teacher_course || ''
    }
    currentPage.value = 1

    if (selectedStudent.value) {
      const latest = tableData.value.find((item) => Number(item.student_id) === Number(selectedStudent.value.student_id))
      if (latest) {
        selectedStudent.value = latest
      }
    }
  } finally {
    loading.value = false
  }
}

const viewDetail = async (row) => {
  try {
    selectedStudent.value = row
    detailLoading.value = true
    detailPlanPage.value = 1
    detailTaskPage.value = 1
    detailProgressPage.value = 1
    const res = await getTeacherStudentLearningPlanDetailApi(row.student_id)
    detail.summary = res.data?.summary || { plan_count: 0, task_total: 0, task_done: 0, total_minutes: 0, completion_rate: 0 }
    detail.plans = res.data?.plans || []
    detail.tasks = res.data?.tasks || []
    detail.progress = res.data?.progress || []
  } finally {
    detailLoading.value = false
  }
}

const handleOverviewRowClick = (row) => {
  viewDetail(row)
}

const openTaskCreate = () => {
  if (!selectedStudent.value || !detail.plans.length) {
    ElMessage.warning('当前学员暂无可用计划，请先导入或创建计划')
    return
  }
  taskForm.plan_id = detail.plans[0].id
  taskForm.task_title = ''
  taskForm.task_date = ''
  taskForm.estimated_minutes = 60
  taskDialogVisible.value = true
}

const submitTaskCreate = async () => {
  if (!taskForm.plan_id || !taskForm.task_title) {
    ElMessage.warning('请至少填写所属计划和任务标题')
    return
  }

  await createTeacherLearningTaskApi({
    plan_id: taskForm.plan_id,
    task_title: taskForm.task_title,
    task_date: taskForm.task_date,
    estimated_minutes: taskForm.estimated_minutes
  })
  ElMessage.success('老师任务创建成功')
  taskDialogVisible.value = false
  if (selectedStudent.value) {
    await viewDetail(selectedStudent.value)
  }
  await loadData()
}

const openImport = (row = null) => {
  form.student_ids = row ? [row.student_id] : []
  form.title = ''
  form.target = ''
  form.start_date = ''
  form.end_date = ''
  taskTemplateText.value = ''
  dialogVisible.value = true
}

const parseTemplateTasks = () => {
  return taskTemplateText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const pieces = line.split('|').map((item) => item.trim())
      if (pieces.length === 1) {
        return pieces[0]
      }
      const taskTitle = pieces[0]
      const taskDate = pieces[1] || ''
      const estimated = Number(pieces[2] || 0)
      const task = { task_title: taskTitle }
      if (/^\d{4}-\d{2}-\d{2}$/.test(taskDate)) {
        task.task_date = taskDate
      }
      if (Number.isFinite(estimated) && estimated > 0) {
        task.estimated_minutes = Math.min(1440, Math.round(estimated))
      }
      return task
    })
}

const submitImport = async () => {
  if (!form.student_ids.length || !form.title || !form.start_date || !form.end_date) {
    ElMessage.warning('请完整填写模板信息')
    return
  }

  if (form.start_date > form.end_date) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return
  }

  const payload = {
    student_ids: form.student_ids,
    title: form.title,
    target: form.target,
    start_date: form.start_date,
    end_date: form.end_date,
    tasks: parseTemplateTasks()
  }

  if (teacherCourse.value !== '英语' && teacherCourse.value !== '政治') {
    const hasGeneralCourseKeywordConflict = payload.tasks.some((task) => {
      const title = typeof task === 'string' ? task : task.task_title || ''
      return String(title).includes('英语') || String(title).includes('政治')
    })
    if (hasGeneralCourseKeywordConflict) {
      ElMessage.warning(`当前老师课程为${teacherCourse.value || '专业课'}，请使用匹配课程的指导任务标题`)
      return
    }
  }

  const res = await importTeacherLearningPlanTemplateApi(payload)
  ElMessage.success(`学习计划创建完成，新增 ${res.data?.plan_count || 0} 条计划`)
  dialogVisible.value = false
  await loadData()
  if (selectedStudent.value) {
    await viewDetail(selectedStudent.value)
  }
}

loadData()
</script>

<style scoped>
.mb12 {
  margin-bottom: 12px;
}

.stat-card {
  min-height: 98px;
}

.sub-text {
  color: #909399;
  font-size: 12px;
  margin-top: 6px;
}

.detail-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.summary-box {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fafcff;
}

.summary-label {
  color: #909399;
  font-size: 12px;
}

.summary-value {
  margin-top: 6px;
  color: #303133;
  font-size: 18px;
  font-weight: 700;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 991px) {
  .detail-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
