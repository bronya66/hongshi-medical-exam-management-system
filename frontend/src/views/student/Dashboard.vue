<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :xs="12" :sm="12" :md="6" v-for="card in statCards" :key="card.label">
        <el-card class="page-card stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card class="page-card" v-loading="loading">
          <template #header><div class="card-title">作业提交情况</div></template>
          <div ref="homeworkChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="page-card" v-loading="loading">
          <template #header><div class="card-title">学习活跃趋势</div></template>
          <div ref="trendChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  getStudentCheckinListApi,
  getStudentEvaluationListApi,
  getStudentHomeworkList,
  getStudentMaterialsList
} from '../../api/student'

const loading = ref(false)
const homeworkList = ref([])
const checkinList = ref([])
const materialsList = ref([])
const evaluationList = ref([])

const homeworkChartRef = ref(null)
const trendChartRef = ref(null)
let homeworkChart = null
let trendChart = null

const statCards = computed(() => {
  const submittedHomework = homeworkList.value.filter((item) => item.submission_id).length
  return [
    { label: '作业总数', value: homeworkList.value.length },
    { label: '已提交作业', value: submittedHomework },
    { label: '打卡次数', value: checkinList.value.length },
    { label: '资料总数', value: materialsList.value.length },
    { label: '评价次数', value: evaluationList.value.length }
  ]
})

const renderCharts = () => {
  if (!homeworkChartRef.value || !trendChartRef.value) return

  if (!homeworkChart) homeworkChart = echarts.init(homeworkChartRef.value)
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  const submitted = homeworkList.value.filter((item) => item.submission_id).length
  const unsubmitted = Math.max(homeworkList.value.length - submitted, 0)

  homeworkChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '作业状态',
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { value: submitted, name: '已提交' },
          { value: unsubmitted, name: '未提交' }
        ],
        label: { color: '#262626' }
      }
    ]
  })

  const trendMap = new Map()
  checkinList.value.slice(0, 14).forEach((item) => {
    const key = String(item.checkin_date || '').slice(0, 10)
    trendMap.set(key, (trendMap.get(key) || 0) + 1)
  })

  const sortedDays = [...trendMap.keys()].sort()
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: sortedDays, axisLabel: { color: '#8c8c8c' } },
    yAxis: { type: 'value', axisLabel: { color: '#8c8c8c' } },
    grid: { left: 36, right: 20, top: 22, bottom: 28 },
    series: [
      {
        name: '打卡次数',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        itemStyle: { color: '#1890ff' },
        areaStyle: { color: 'rgba(24,144,255,0.14)' },
        data: sortedDays.map((day) => trendMap.get(day))
      }
    ]
  })
}

const loadData = async () => {
  try {
    loading.value = true
    const [homeworkRes, checkinRes, materialsRes, evaluationRes] = await Promise.all([
      getStudentHomeworkList(),
      getStudentCheckinListApi(),
      getStudentMaterialsList(),
      getStudentEvaluationListApi()
    ])
    homeworkList.value = homeworkRes.data || []
    checkinList.value = checkinRes.data || []
    materialsList.value = materialsRes.data || []
    evaluationList.value = evaluationRes.data || []
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

const onResize = () => {
  homeworkChart?.resize()
  trendChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  homeworkChart?.dispose()
  trendChart?.dispose()
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
