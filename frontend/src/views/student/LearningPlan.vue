<template>
  <div class="page-shell">
    <el-row :gutter="16" class="mb12">
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="学习计划" :value="overview.planTotal" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="任务完成率" :value="overview.completionRate" suffix="%" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="累计学习分钟" :value="overview.totalMinutes" />
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card class="page-card stat-card">
          <el-statistic title="当前计划记录天数" :value="progressSummary.record_days || 0" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="10">
        <el-card class="page-card">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">计划列表</div>
              <el-button type="primary" @click="openPlanCreate">新建计划</el-button>
            </div>
          </template>

          <el-form :inline="true" class="mb12">
            <el-form-item label="关键词">
              <el-input v-model.trim="planFilter.keyword" placeholder="计划标题或目标" style="width: 190px" @input="currentPage = 1" />
            </el-form-item>
          </el-form>

          <el-table class="page-table" :data="pagedPlanList" border stripe table-layout="auto" max-height="460" v-loading="loading" row-key="id" highlight-current-row @row-click="selectPlan">
            <el-table-column prop="title" label="计划" min-width="150" />
            <el-table-column label="周期" min-width="170">
              <template #default="{ row }">{{ formatDisplayDate(row.start_date) }} ~ {{ formatDisplayDate(row.end_date) }}</template>
            </el-table-column>
            <el-table-column label="完成" width="95">
              <template #default="{ row }">{{ row.task_done || 0 }}/{{ row.task_total || 0 }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="openPlanEdit(row)">编辑</el-button>
                <el-button link type="danger" @click.stop="removePlan(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && filteredPlanList.length === 0" description="暂无学习计划" />
          <div class="pagination-wrap" v-if="filteredPlanList.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredPlanList.length"
              @current-change="(page) => (currentPage = page)"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card class="page-card" v-if="currentPlan">
          <template #header>
            <div class="header-wrap">
              <div>
                <div class="card-title">{{ currentPlan.title }}</div>
                <div class="plan-sub">{{ currentPlan.target || '未填写目标' }}</div>
              </div>
              <el-space wrap>
                <el-tag type="info">周期 {{ formatDisplayDate(currentPlan.start_date) }} ~ {{ formatDisplayDate(currentPlan.end_date) }}</el-tag>
                <el-tag type="success">累计 {{ progressSummary.total_minutes || 0 }} 分钟</el-tag>
                <el-button type="primary" @click="openTaskCreate">新增任务</el-button>
              </el-space>
            </div>
          </template>

          <el-form :inline="true" class="mb12" @submit.prevent>
            <el-form-item label="今日学习时长(分钟)">
              <el-input-number v-model="todayProgress.study_minutes" :min="0" :max="1440" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model.trim="todayProgress.note" placeholder="今日复盘" style="width: 230px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProgress">记录进度</el-button>
            </el-form-item>
          </el-form>

          <div class="task-table-head">
            <span>任务总数：{{ taskList.length }}</span>
            <span class="task-table-tip">任务较多时可在表格内滚动查看</span>
          </div>

          <el-table class="page-table" :data="taskList" border stripe table-layout="auto" max-height="460" v-loading="taskLoading">
            <el-table-column prop="task_title" label="任务" min-width="180" />
            <el-table-column label="日期" width="120">
              <template #default="{ row }">{{ formatDisplayDate(row.task_date) }}</template>
            </el-table-column>
            <el-table-column prop="estimated_minutes" label="预计时长" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-switch :model-value="Boolean(row.is_done)" @change="toggleTaskDone(row, $event)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="danger" @click="removeTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

        </el-card>

        <el-card class="page-card" v-else>
          <el-empty description="请先选择一个学习计划" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="planDialogVisible" :title="editingPlanId ? '编辑学习计划' : '新建学习计划'" width="620px">
      <el-form :model="planForm" label-width="100px">
        <el-form-item label="计划标题">
          <el-input v-model.trim="planForm.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="学习目标">
          <el-input v-model.trim="planForm.target" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="planForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="planForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="提醒时间">
          <el-time-picker v-model="planForm.remind_time" value-format="HH:mm:ss" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="taskDialogVisible" title="新增学习任务" width="560px">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务标题">
          <el-input v-model.trim="taskForm.task_title" maxlength="160" show-word-limit />
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
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createStudentLearningPlanApi,
  createStudentLearningTaskApi,
  deleteStudentLearningPlanApi,
  deleteStudentLearningTaskApi,
  getStudentLearningPlanListApi,
  getStudentLearningTaskListApi,
  getStudentPlanProgressStatApi,
  updateStudentLearningPlanApi,
  updateStudentLearningTaskApi,
  upsertStudentPlanProgressApi
} from '../../api/student'

const loading = ref(false)
const taskLoading = ref(false)
const planList = ref([])
const taskList = ref([])
const currentPlan = ref(null)
const progressSummary = ref({ total_minutes: 0, record_days: 0, avg_minutes: 0 })

const planDialogVisible = ref(false)
const taskDialogVisible = ref(false)
const editingPlanId = ref(null)
const currentPage = ref(1)
const pageSize = ref(8)

const todayProgress = reactive({
  study_minutes: 120,
  note: ''
})

const planForm = reactive({
  title: '',
  target: '',
  start_date: '',
  end_date: '',
  remind_time: ''
})

const taskForm = reactive({
  task_title: '',
  task_date: '',
  estimated_minutes: 60
})

const planFilter = reactive({
  keyword: ''
})

const overview = computed(() => {
  const planTotal = planList.value.length
  const taskTotal = planList.value.reduce((sum, item) => sum + Number(item.task_total || 0), 0)
  const taskDone = planList.value.reduce((sum, item) => sum + Number(item.task_done || 0), 0)
  const totalMinutes = planList.value.reduce((sum, item) => sum + Number(item.total_minutes || 0), 0)
  const completionRate = taskTotal ? Number(((taskDone / taskTotal) * 100).toFixed(1)) : 0
  return { planTotal, completionRate, totalMinutes }
})

const filteredPlanList = computed(() => {
  const keyword = planFilter.keyword.toLowerCase()
  return planList.value.filter((item) => {
    if (!keyword) return true
    const title = String(item.title || '').toLowerCase()
    const target = String(item.target || '').toLowerCase()
    return title.includes(keyword) || target.includes(keyword)
  })
})

const pagedPlanList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredPlanList.value.slice(start, start + pageSize.value)
})

const resetPlanForm = () => {
  planForm.title = ''
  planForm.target = ''
  planForm.start_date = ''
  planForm.end_date = ''
  planForm.remind_time = ''
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

  const chineseDateMatch = text.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日$/)
  if (chineseDateMatch) {
    const [, y, m, d] = chineseDateMatch
    return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  }

  return ''
}

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

const loadPlans = async () => {
  try {
    loading.value = true
    const res = await getStudentLearningPlanListApi()
    planList.value = res.data || []

    if (!planList.value.length) {
      currentPlan.value = null
      taskList.value = []
      progressSummary.value = { total_minutes: 0, record_days: 0, avg_minutes: 0 }
      return
    }

    const currentId = Number(currentPlan.value?.id || 0)
    const matched = planList.value.find((item) => Number(item.id) === currentId)
    await selectPlan(matched || planList.value[0])
  } finally {
    loading.value = false
  }
}

const selectPlan = async (plan) => {
  if (!plan) return
  currentPlan.value = plan
  await loadTasks(plan.id)
  await loadProgress(plan.id)
}

const loadTasks = async (planId) => {
  try {
    taskLoading.value = true
    const res = await getStudentLearningTaskListApi(planId)
    taskList.value = (res.data || []).map((item) => ({
      ...item,
      task_date: normalizeDateForApi(item.task_date)
    }))
  } finally {
    taskLoading.value = false
  }
}

const loadProgress = async (planId) => {
  const res = await getStudentPlanProgressStatApi(planId)
  progressSummary.value = res.data?.summary || { total_minutes: 0, record_days: 0, avg_minutes: 0 }
}

const openPlanCreate = () => {
  editingPlanId.value = null
  resetPlanForm()
  planDialogVisible.value = true
}

const openPlanEdit = (row) => {
  editingPlanId.value = row.id
  planForm.title = row.title || ''
  planForm.target = row.target || ''
  planForm.start_date = normalizeDateForApi(row.start_date)
  planForm.end_date = normalizeDateForApi(row.end_date)
  planForm.remind_time = row.remind_time || ''
  planDialogVisible.value = true
}

const savePlan = async () => {
  if (!planForm.title || !planForm.start_date || !planForm.end_date) {
    ElMessage.warning('请完整填写计划信息')
    return
  }
  if (planForm.start_date > planForm.end_date) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return
  }

  if (editingPlanId.value) {
    await updateStudentLearningPlanApi(editingPlanId.value, { ...planForm })
    ElMessage.success('计划已更新')
  } else {
    await createStudentLearningPlanApi({ ...planForm })
    ElMessage.success('计划创建成功')
  }

  planDialogVisible.value = false
  await loadPlans()
}

const removePlan = async (row) => {
  await ElMessageBox.confirm(`确认删除学习计划：${row.title}？`, '提示', { type: 'warning' })
  await deleteStudentLearningPlanApi(row.id)
  ElMessage.success('删除成功')
  if (Number(currentPlan.value?.id) === Number(row.id)) {
    currentPlan.value = null
  }
  await loadPlans()
}

const openTaskCreate = () => {
  if (!currentPlan.value) return
  taskForm.task_title = ''
  taskForm.task_date = ''
  taskForm.estimated_minutes = 60
  taskDialogVisible.value = true
}

const saveTask = async () => {
  if (!currentPlan.value) return
  if (!taskForm.task_title) {
    ElMessage.warning('请输入任务标题')
    return
  }

  await createStudentLearningTaskApi({
    plan_id: currentPlan.value.id,
    task_title: taskForm.task_title,
    task_date: taskForm.task_date,
    estimated_minutes: taskForm.estimated_minutes
  })
  ElMessage.success('任务创建成功')
  taskDialogVisible.value = false
  await loadTasks(currentPlan.value.id)
  await loadPlans()
}

const toggleTaskDone = async (row, checked) => {
  if (!currentPlan.value) return
  await updateStudentLearningTaskApi(row.id, {
    task_title: row.task_title,
    task_date: normalizeDateForApi(row.task_date),
    estimated_minutes: row.estimated_minutes,
    sort_no: row.sort_no,
    is_done: checked ? 1 : 0
  })
  ElMessage.success(checked ? '任务已完成' : '任务已恢复未完成')
  await loadTasks(currentPlan.value.id)
  await loadPlans()
}

const removeTask = async (row) => {
  if (!currentPlan.value) return
  await deleteStudentLearningTaskApi(row.id)
  ElMessage.success('任务已删除')
  await loadTasks(currentPlan.value.id)
  await loadPlans()
}

const saveProgress = async () => {
  if (!currentPlan.value) return
  await upsertStudentPlanProgressApi({
    plan_id: currentPlan.value.id,
    study_minutes: todayProgress.study_minutes,
    note: todayProgress.note
  })
  ElMessage.success('今日进度已记录')
  todayProgress.note = ''
  await loadProgress(currentPlan.value.id)
  await loadPlans()
}

loadPlans()
</script>

<style scoped>
.mb12 {
  margin-bottom: 12px;
}

.stat-card {
  min-height: 98px;
}

.plan-sub {
  margin-top: 4px;
  color: #8c8c8c;
  font-size: 12px;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.task-table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: #606266;
  font-size: 13px;
}

.task-table-tip {
  color: #909399;
}
</style>

