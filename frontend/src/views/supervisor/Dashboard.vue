<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :xs="12" :sm="12" :md="6" v-for="card in statCards" :key="card.label">
        <el-card class="page-card stat-card" v-loading="loading">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card class="page-card" v-loading="loading">
          <template #header><div class="card-title">打卡状态分布</div></template>
          <div ref="checkinChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="page-card" v-loading="evaluationLoading">
          <template #header><div class="card-title">教师平均分对比</div></template>
          <div ref="evaluationChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getSupervisorCheckinStat, getSupervisorEvaluationStat } from '../../api/supervisor'

const loading = ref(false)
const evaluationLoading = ref(false)
const checkinStat = ref({
  totalStudents: 0,
  checkedToday: 0,
  uncheckedToday: 0,
  checkinRate: 0
})
const evaluationList = ref([])

const checkinChartRef = ref(null)
const evaluationChartRef = ref(null)
let checkinChart = null
let evaluationChart = null

const statCards = computed(() => [
  { label: '学员总数', value: checkinStat.value.totalStudents || 0 },
  { label: '今日已打卡', value: checkinStat.value.checkedToday || 0 },
  { label: '今日未打卡', value: checkinStat.value.uncheckedToday || 0 },
  { label: '打卡率', value: `${Number(checkinStat.value.checkinRate || 0).toFixed(2)}%` }
])

const renderCharts = () => {
  if (!checkinChartRef.value || !evaluationChartRef.value) return
  if (!checkinChart) checkinChart = echarts.init(checkinChartRef.value)
  if (!evaluationChart) evaluationChart = echarts.init(evaluationChartRef.value)

  checkinChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '打卡状态',
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { name: '已打卡', value: checkinStat.value.checkedToday || 0 },
          { name: '未打卡', value: checkinStat.value.uncheckedToday || 0 }
        ]
      }
    ]
  })

  evaluationChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: evaluationList.value.map((item) => item.teacher_username || `教师${item.teacher_id}`),
      axisLabel: { color: '#8c8c8c' }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
      axisLabel: { color: '#8c8c8c' }
    },
    grid: { left: 36, right: 20, top: 22, bottom: 28 },
    series: [
      {
        type: 'bar',
        barWidth: 24,
        itemStyle: { color: '#52c41a', borderRadius: [8, 8, 0, 0] },
        data: evaluationList.value.map((item) => Number(item.avg_score || 0))
      }
    ]
  })
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getSupervisorCheckinStat()
    checkinStat.value = res.data?.stat || checkinStat.value
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

const loadEvaluation = async () => {
  try {
    evaluationLoading.value = true
    const res = await getSupervisorEvaluationStat()
    evaluationList.value = res.data || []
    await nextTick()
    renderCharts()
  } finally {
    evaluationLoading.value = false
  }
}

const onResize = () => {
  checkinChart?.resize()
  evaluationChart?.resize()
}

onMounted(() => {
  loadData()
  loadEvaluation()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  checkinChart?.dispose()
  evaluationChart?.dispose()
})
</script>

<style scoped>
.stat-card {
  margin-bottom: 16px;
}

.stat-label {
  color: #8c8c8c;
  font-size: 13px;
}

.stat-value {
  margin-top: 8px;
  font-size: 28px;
  line-height: 1;
  font-weight: 800;
  color: #262626;
}

.chart-box {
  height: 300px;
}
</style>
