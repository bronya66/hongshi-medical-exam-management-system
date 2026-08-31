<template>
	<div class="dashboard-wrap">
		<el-card class="hero-card" shadow="never" v-loading="loading">
			<div class="hero-title">系统总览</div>
			<div class="hero-sub">统一观察用户规模、学习行为与教学数据变化</div>
			<div class="hero-total">总记录数：{{ totalCount }}</div>
		</el-card>

		<el-row :gutter="16" class="stats-grid">
			<el-col :xs="12" :sm="12" :md="8" :lg="4" :xl="4" v-for="card in statCards" :key="card.label">
				<el-card class="stat-card" shadow="hover" v-loading="loading">
					<div class="stat-title">{{ card.label }}</div>
					<div class="stat-value">{{ card.value }}</div>
				</el-card>
			</el-col>
		</el-row>

		<el-row :gutter="16">
			<el-col :xs="24" :lg="12">
				<el-card class="chart-card" shadow="hover" v-loading="loading">
					<template #header><div class="card-title">核心业务结构占比</div></template>
					<div ref="pieRef" class="chart-box"></div>
				</el-card>
			</el-col>
			<el-col :xs="24" :lg="12">
				<el-card class="chart-card" shadow="hover" v-loading="loading">
					<template #header><div class="card-title">业务记录规模对比</div></template>
					<div ref="barRef" class="chart-box"></div>
				</el-card>
			</el-col>
		</el-row>
	</div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { getAdminStatsApi } from '../../api/admin'

const loading = ref(false)
const pieRef = ref(null)
const barRef = ref(null)
let pieChart = null
let barChart = null
let chartLibPromise = null

const stats = reactive({
	userTotal: 0,
	studentTotal: 0,
	checkinTotal: 0,
	homeworkTotal: 0,
	materialsTotal: 0,
	evaluationTotal: 0,
	adminUserTotal: 0
})

const statCards = computed(() => [
	{ label: '管理员', value: stats.adminUserTotal || 0 },
	{ label: '系统用户', value: stats.userTotal || 0 },
	{ label: '学员总数', value: stats.studentTotal || 0 },
	{ label: '打卡记录', value: stats.checkinTotal || 0 },
	{ label: '作业记录', value: stats.homeworkTotal || 0 },
	{ label: '资料记录', value: stats.materialsTotal || 0 }
])

const totalCount = computed(() => {
	return (
		(stats.adminUserTotal || 0) +
		(stats.userTotal || 0) +
		(stats.studentTotal || 0) +
		(stats.checkinTotal || 0) +
		(stats.homeworkTotal || 0) +
		(stats.materialsTotal || 0) +
		(stats.evaluationTotal || 0)
	)
})

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
				charts.BarChart,
				components.TooltipComponent,
				components.LegendComponent,
				components.GridComponent,
				renderers.CanvasRenderer
			])
			return core
		})
	}

	return chartLibPromise
}


const renderCharts = async () => {
	if (!pieRef.value || !barRef.value) return
	const chartLib = await ensureChartLib()

	if (!pieChart) pieChart = chartLib.init(pieRef.value)
	if (!barChart) barChart = chartLib.init(barRef.value)

	pieChart.setOption({
		tooltip: { trigger: 'item' },
		legend: { bottom: 0 },
		series: [
			{
				type: 'pie',
				radius: ['42%', '68%'],
				data: [
					{ name: '打卡', value: stats.checkinTotal || 0 },
					{ name: '作业', value: stats.homeworkTotal || 0 },
					{ name: '资料', value: stats.materialsTotal || 0 },
					{ name: '评价', value: stats.evaluationTotal || 0 }
				]
			}
		]
	})

	barChart.setOption({
		tooltip: { trigger: 'axis' },
		xAxis: {
			type: 'category',
			axisLabel: { color: '#8c8c8c' },
			data: ['管理员', '用户', '学员', '打卡', '作业', '资料', '评价']
		},
		yAxis: { type: 'value', axisLabel: { color: '#8c8c8c' } },
		grid: { left: 36, right: 20, top: 22, bottom: 28 },
		series: [
			{
				type: 'bar',
				barWidth: 24,
				itemStyle: { color: '#1890ff', borderRadius: [8, 8, 0, 0] },
				data: [
					stats.adminUserTotal || 0,
					stats.userTotal || 0,
					stats.studentTotal || 0,
					stats.checkinTotal || 0,
					stats.homeworkTotal || 0,
					stats.materialsTotal || 0,
					stats.evaluationTotal || 0
				]
			}
		]
	})
}

const onResize = () => {
	pieChart?.resize()
	barChart?.resize()
}

const loadData = async () => {

	try {
		loading.value = true
		const res = await getAdminStatsApi()
		Object.assign(stats, res.data || {})
		await nextTick()
		await renderCharts()
	} finally {
		loading.value = false
	}
}

onMounted(() => {
	loadData()
	window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
	window.removeEventListener('resize', onResize)
	pieChart?.dispose()
	barChart?.dispose()
})
</script>

<style scoped>
.dashboard-wrap {
	display: grid;
	gap: 16px;
}

.hero-card {
	border-radius: 16px;
	border: 1px solid #dbe7fb;
	background: linear-gradient(120deg, #e9f3ff, #f8fcff);
}

.hero-title {
	font-size: 20px;
	font-weight: 800;
	color: #1d3b73;
}

.hero-sub {
	margin-top: 6px;
	font-size: 13px;
	color: #5b6c8f;
}

.hero-total {
	margin-top: 10px;
	color: #2f84ff;
	font-weight: 700;
}

.stats-grid {
	margin-bottom: 0;
}

.stat-card {
	border-radius: 14px;
	border: 1px solid #e6ecfb;
}

.stat-title {
	color: #5f6e8d;
	font-size: 13px;
	margin-bottom: 10px;
}

.stat-value {
	font-size: 28px;
	line-height: 1;
	font-weight: 800;
	color: #1f2a44;
}

.chart-card {
	border-radius: 14px;
	border: 1px solid #e6ecfb;
}

.card-title {
	font-weight: 700;
}

.chart-box {
	height: 320px;
}
</style>
