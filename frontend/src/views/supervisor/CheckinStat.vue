<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">打卡率统计</div>
          </template>
          <div ref="chartRef" class="chart-box" v-loading="loading" />
          <div class="stat-line">
            <el-tag type="success">今日打卡率：{{ rateText }}</el-tag>
            <el-tag type="warning">未打卡人数：{{ stat.uncheckedToday }}</el-tag>
            <el-button type="primary" :loading="remindLoading" @click="handleRemindUnchecked">提醒未打卡学员</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">未打卡学员提醒</div>
          </template>
          <el-empty v-if="!loading && uncheckedList.length === 0" description="今日全部已打卡" />
          <el-space v-else wrap class="unchecked-tags">
            <el-tag v-for="item in uncheckedList" :key="item.student_id" type="danger">
              {{ item.student_name }}（{{ item.username }}）
            </el-tag>
          </el-space>

          <el-divider />

          <div class="card-title mb12">评价统计（按老师）</div>
          <el-table class="page-table" :data="evaluationData" border stripe table-layout="auto" v-loading="evaluationLoading">
            <el-table-column prop="teacher_id" label="老师ID" min-width="90" />
            <el-table-column prop="teacher_username" label="老师账号" min-width="130" />
            <el-table-column prop="evaluation_count" label="评价数" min-width="90" />
            <el-table-column prop="avg_score" label="平均分" min-width="90" />
          </el-table>
          <el-empty v-if="!evaluationLoading && evaluationData.length === 0" description="暂无评价统计" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="page-card" style="margin-top: 16px">
      <template #header>
        <div class="card-title">学员打卡明细</div>
      </template>
      <el-form :inline="true" class="mb12">
        <el-form-item label="关键词">
          <el-input v-model.trim="filter.keyword" placeholder="姓名/账号" style="width: 180px" @input="currentPage = 1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" style="width: 140px" @change="currentPage = 1">
            <el-option label="全部" value="all" />
            <el-option label="已打卡" value="checked" />
            <el-option label="未打卡" value="unchecked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="student_id" label="学员ID" min-width="80" />
        <el-table-column prop="username" label="账号" min-width="120" />
        <el-table-column prop="student_name" label="姓名" min-width="120" />
        <el-table-column prop="checkin_count" label="累计打卡次数" min-width="120" />
        <el-table-column prop="last_checkin_date" label="最近打卡日期" min-width="130" />
        <el-table-column label="今日状态" min-width="110">
          <template #default="{ row }">
            <el-tag :type="isCheckedToday(row) ? 'success' : 'danger'">
              {{ isCheckedToday(row) ? '已打卡' : '未打卡' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无打卡记录" />
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
  </div>
</template>

<script setup>
// 督学统计页：
// 1. 展示打卡率图表（ECharts）
// 2. 展示未打卡提醒
// 3. 展示老师评价统计

import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSupervisorCheckinStat, getSupervisorEvaluationStat, remindSupervisorUncheckedApi } from '../../api/supervisor'

const tableData = ref([])
const loading = ref(true)
const remindLoading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let chartLibPromise = null

const evaluationData = ref([])
const evaluationLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const filter = reactive({
  keyword: '',
  status: 'all'
})

const stat = reactive({
  totalStudents: 0,
  checkedToday: 0,
  uncheckedToday: 0,
  checkinRate: 0,
  date: ''
})

const getLocalDateString = () => {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const normalizeDateString = (value) => {
  const text = String(value || '').trim()
  if (!text) return ''

  const direct = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (direct) return `${direct[1]}-${direct[2]}-${direct[3]}`

  const nums = text.match(/\d+/g)
  if (nums && nums.length >= 3) {
    const y = String(nums[0]).padStart(4, '0')
    const m = String(nums[1]).padStart(2, '0')
    const d = String(nums[2]).padStart(2, '0')
    return `${y}-${m}-${d}`
  }

  return text
}

const targetDate = computed(() => String(stat.date || getLocalDateString()))

const isCheckedToday = (row) => {
  const lastDate = normalizeDateString(row.last_checkin_date)
  const current = normalizeDateString(targetDate.value)
  return !!lastDate && lastDate === current
}

const uncheckedList = computed(() => tableData.value.filter((item) => !isCheckedToday(item)))
const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  return tableData.value.filter((item) => {
    const checked = isCheckedToday(item)
    if (filter.status === 'checked' && !checked) return false
    if (filter.status === 'unchecked' && checked) return false
    if (!keyword) return true
    const username = String(item.username || '').toLowerCase()
    const studentName = String(item.student_name || '').toLowerCase()
    return username.includes(keyword) || studentName.includes(keyword)
  })
})
const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const rateText = computed(() => `${Number(stat.checkinRate || 0).toFixed(2)}%`)

const ensureChartLib = async () => {
  if (!chartLibPromise) {
    chartLibPromise = Promise.all([
      import('echarts/core'),
      import('echarts/charts'),
      import('echarts/components'),
      import('echarts/renderers')
    ]).then(([core, charts, components, renderers]) => {
      core.use([
        charts.PieChart,
        components.TooltipComponent,
        components.LegendComponent,
        renderers.CanvasRenderer
      ])
      return core
    })
  }

  return chartLibPromise
}

const renderChart = async () => {
  if (!chartRef.value) return
  const chartLib = await ensureChartLib()
  if (!chartInstance) {
    chartInstance = chartLib.init(chartRef.value)
  }

  chartInstance.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '今日打卡',
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { value: stat.checkedToday || 0, name: '已打卡' },
          { value: stat.uncheckedToday || 0, name: '未打卡' }
        ]
      }
    ]
  })
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getSupervisorCheckinStat()
    tableData.value = res.data?.list || []
    currentPage.value = 1
    Object.assign(stat, res.data?.stat || {})
    await nextTick()
    await renderChart()
  } finally {
    loading.value = false
  }
}

const loadEvaluationStat = async () => {
  try {
    evaluationLoading.value = true
    const res = await getSupervisorEvaluationStat()
    evaluationData.value = res.data || []
  } finally {
    evaluationLoading.value = false
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

const handleRemindUnchecked = async () => {
  const targetIds = filteredTableData.value.filter((item) => !isCheckedToday(item)).map((item) => item.student_id)
  if (!targetIds.length) {
    ElMessage.info('当前筛选范围内没有未打卡学员')
    return
  }

  try {
    remindLoading.value = true
    const res = await remindSupervisorUncheckedApi({ student_ids: targetIds })
    const data = res.data || {}
    ElMessage.success(`已提醒 ${data.student_count || 0} 名学员，并同步 ${data.teacher_count || 0} 位任课老师`)
  } finally {
    remindLoading.value = false
  }
}

onMounted(() => {
  loadData()
  loadEvaluationStat()
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.chart-box {
  height: 260px;
}

.stat-line {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mb12 {
  margin-bottom: 12px;
}

.unchecked-tags {
  max-height: 72px;
  overflow: auto;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
