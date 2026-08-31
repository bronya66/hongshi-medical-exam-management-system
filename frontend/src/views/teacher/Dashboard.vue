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
          <template #header><div class="card-title">作业与资料规模</div></template>
          <div ref="barChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="page-card" v-loading="loading">
          <template #header><div class="card-title">评价分布</div></template>
          <div ref="scoreChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  getTeacherEvaluationList,
  getTeacherHomeworkListApi,
  getTeacherMaterialsListApi,
  getTeacherStudentList
} from '../../api/teacher'

const loading = ref(false)
const studentList = ref([])
const homeworkList = ref([])
const materialsList = ref([])
const evaluationList = ref([])

const barChartRef = ref(null)
const scoreChartRef = ref(null)
let barChart = null
let scoreChart = null

const statCards = computed(() => {
  const avgScore = evaluationList.value.length
    ? (evaluationList.value.reduce((sum, item) => sum + Number(item.score || 0), 0) / evaluationList.value.length).toFixed(2)
    : '0.00'

  return [
    { label: '班级学员数', value: studentList.value.length },
    { label: '作业总数', value: homeworkList.value.length },
    { label: '资料总数', value: materialsList.value.length },
    { label: '平均评分', value: avgScore }
  ]
})

const renderCharts = () => {
  if (!barChartRef.value || !scoreChartRef.value) return
  if (!barChart) barChart = echarts.init(barChartRef.value)
  if (!scoreChart) scoreChart = echarts.init(scoreChartRef.value)

  barChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['学员', '作业', '资料', '评价'],
      axisLabel: { color: '#8c8c8c' }
    },
    yAxis: { type: 'value', axisLabel: { color: '#8c8c8c' } },
    grid: { left: 36, right: 20, top: 22, bottom: 28 },
    series: [
      {
        type: 'bar',
        barWidth: 28,
        itemStyle: { color: '#1890ff', borderRadius: [8, 8, 0, 0] },
        data: [studentList.value.length, homeworkList.value.length, materialsList.value.length, evaluationList.value.length]
      }
    ]
  })

  const scoreMap = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
  evaluationList.value.forEach((item) => {
    const score = Number(item.score || 0)
    if (scoreMap[score] !== undefined) scoreMap[score] += 1
  })

  scoreChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '评分分布',
        type: 'pie',
        radius: ['45%', '70%'],
        data: Object.keys(scoreMap).map((key) => ({ name: `${key}星`, value: scoreMap[key] }))
      }
    ]
  })
}

const loadData = async () => {
  try {
    loading.value = true
    const [studentRes, homeworkRes, materialsRes, evaluationRes] = await Promise.all([
      getTeacherStudentList(),
      getTeacherHomeworkListApi(),
      getTeacherMaterialsListApi(),
      getTeacherEvaluationList()
    ])
    studentList.value = studentRes.data || []
    homeworkList.value = homeworkRes.data || []
    materialsList.value = materialsRes.data || []
    evaluationList.value = evaluationRes.data || []

    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

const onResize = () => {
  barChart?.resize()
  scoreChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  barChart?.dispose()
  scoreChart?.dispose()
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
