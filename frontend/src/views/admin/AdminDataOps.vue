<template>
	<el-card class="page-card">
		<template #header>
			<div class="card-title">数据批量操作</div>
		</template>

		<el-tabs v-model="activeTab" @tab-change="loadCurrent">
			<el-tab-pane label="打卡数据" name="checkin" />
			<el-tab-pane label="作业数据" name="homework" />
			<el-tab-pane label="资料数据" name="materials" />
			<el-tab-pane label="评价数据" name="evaluation" />
		</el-tabs>

		<div class="toolbar mb12">
			<el-button type="primary" @click="handleExport">导出当前数据</el-button>
			<el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
		</div>

		<el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading" @selection-change="onSelectionChange">
			<el-table-column type="selection" width="55" />
			<el-table-column v-for="col in columns" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.minWidth || 130">
				<template #default="{ row }">
					{{ formatCellValue(row, col.prop) }}
				</template>
			</el-table-column>
		</el-table>
		<el-empty v-if="!loading && tableData.length === 0" description="暂无数据" />
		<div class="pagination-wrap" v-if="tableData.length > 0">
			<el-pagination
				background
				layout="prev, pager, next, total"
				:current-page="currentPage"
				:page-size="pageSize"
				:total="tableData.length"
				@current-change="handlePageChange"
			/>
		</div>
	</el-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
	adminDeleteCheckinBatchApi,
	adminDeleteEvaluationBatchApi,
	adminDeleteHomeworkBatchApi,
	adminDeleteMaterialsBatchApi,
	getAdminCheckinExportUrl,
	getAdminCheckinListApi,
	getAdminEvaluationExportUrl,
	getAdminEvaluationListApi,
	getAdminHomeworkExportUrl,
	getAdminHomeworkListApi,
	getAdminMaterialsExportUrl,
	getAdminMaterialsListApi
} from '../../api/admin'

const activeTab = ref('checkin')
const loading = ref(false)
const tableData = ref([])
const selectedIds = ref([])
const currentPage = ref(1)
const pageSize = 12

const columnsMap = {
	checkin: [
		{ prop: 'student_name', label: '学员姓名', minWidth: 120 },
		{ prop: 'content', label: '打卡内容', minWidth: 220 },
		{ prop: 'file_path', label: '附件路径', minWidth: 180 },
		{ prop: 'checkin_date', label: '打卡日期', minWidth: 130 },
		{ prop: 'create_time', label: '创建时间', minWidth: 160 }
	],
	homework: [
		{ prop: 'teacher_name', label: '老师姓名', minWidth: 120 },
		{ prop: 'title', label: '作业标题', minWidth: 180 },
		{ prop: 'content', label: '作业内容', minWidth: 220 },
		{ prop: 'publish_time', label: '发布时间', minWidth: 160 },
		{ prop: 'deadline', label: '截止时间', minWidth: 160 }
	],
	materials: [
		{ prop: 'teacher_name', label: '老师姓名', minWidth: 120 },
		{ prop: 'title', label: '资料标题', minWidth: 180 },
		{ prop: 'file_path', label: '文件路径', minWidth: 200 },
		{ prop: 'download_count', label: '下载次数', minWidth: 110 },
		{ prop: 'upload_time', label: '上传时间', minWidth: 160 }
	],
	evaluation: [
		{ prop: 'student_name', label: '学员姓名', minWidth: 120 },
		{ prop: 'teacher_name', label: '老师姓名', minWidth: 120 },
		{ prop: 'score', label: '评分', minWidth: 90 },
		{ prop: 'content', label: '评价内容', minWidth: 220 },
		{ prop: 'create_time', label: '创建时间', minWidth: 160 }
	]
}

const columns = computed(() => columnsMap[activeTab.value] || [])
const pagedTableData = computed(() => {
	const start = (currentPage.value - 1) * pageSize
	return tableData.value.slice(start, start + pageSize)
})

const formatCellValue = (row, prop) => {
	const value = row?.[prop]
	if (prop === 'file_path') {
		return value && String(value).trim() ? value : '无附件'
	}
	return value ?? '-'
}

const parseDateTime = (value) => {
	if (!value) return 0
	const normalized = String(value)
		.replace(/年|\//g, '-')
		.replace(/月/g, '-')
		.replace(/日/g, '')
		.trim()
	const timestamp = new Date(normalized).getTime()
	return Number.isNaN(timestamp) ? 0 : timestamp
}

const sortRowsByTimeDesc = (rows) => {
	const list = Array.isArray(rows) ? [...rows] : []
	if (activeTab.value === 'checkin') {
		return list.sort((left, right) => {
			const diff = parseDateTime(right.create_time || right.checkin_date) - parseDateTime(left.create_time || left.checkin_date)
			if (diff !== 0) return diff
			return Number(right.id || 0) - Number(left.id || 0)
		})
	}
	if (activeTab.value === 'homework') {
		return list.sort((left, right) => {
			const diff = parseDateTime(right.publish_time || right.deadline) - parseDateTime(left.publish_time || left.deadline)
			if (diff !== 0) return diff
			return Number(right.id || 0) - Number(left.id || 0)
		})
	}
	if (activeTab.value === 'materials') {
		return list.sort((left, right) => {
			const diff = parseDateTime(right.upload_time) - parseDateTime(left.upload_time)
			if (diff !== 0) return diff
			return Number(right.id || 0) - Number(left.id || 0)
		})
	}
	return list.sort((left, right) => {
		const diff = parseDateTime(right.create_time) - parseDateTime(left.create_time)
		if (diff !== 0) return diff
		return Number(right.id || 0) - Number(left.id || 0)
	})
}

const loadCurrent = async () => {
	selectedIds.value = []
	try {
		loading.value = true
		if (activeTab.value === 'checkin') {
			const res = await getAdminCheckinListApi()
			tableData.value = sortRowsByTimeDesc(res.data || [])
		} else if (activeTab.value === 'homework') {
			const res = await getAdminHomeworkListApi()
			tableData.value = sortRowsByTimeDesc(res.data || [])
		} else if (activeTab.value === 'materials') {
			const res = await getAdminMaterialsListApi()
			tableData.value = sortRowsByTimeDesc(res.data || [])
		} else {
			const res = await getAdminEvaluationListApi()
			tableData.value = sortRowsByTimeDesc(res.data || [])
		}
		currentPage.value = 1
	} finally {
		loading.value = false
	}
}

const onSelectionChange = (rows) => {
	selectedIds.value = rows.map((item) => item.id)
}

const handlePageChange = (page) => {
	currentPage.value = page
}

const handleExport = () => {
	let url = ''
	if (activeTab.value === 'checkin') url = getAdminCheckinExportUrl()
	if (activeTab.value === 'homework') url = getAdminHomeworkExportUrl()
	if (activeTab.value === 'materials') url = getAdminMaterialsExportUrl()
	if (activeTab.value === 'evaluation') url = getAdminEvaluationExportUrl()
	window.open(url, '_blank')
}

const handleBatchDelete = async () => {
	if (!selectedIds.value.length) {
		ElMessage.warning('请先勾选需要删除的数据')
		return
	}

	await ElMessageBox.confirm('确认批量删除当前选中数据？', '提示', { type: 'warning' })

	if (activeTab.value === 'checkin') {
		await adminDeleteCheckinBatchApi(selectedIds.value)
	} else if (activeTab.value === 'homework') {
		await adminDeleteHomeworkBatchApi(selectedIds.value)
	} else if (activeTab.value === 'materials') {
		await adminDeleteMaterialsBatchApi(selectedIds.value)
	} else {
		await adminDeleteEvaluationBatchApi(selectedIds.value)
	}

	ElMessage.success('批量删除成功')
	loadCurrent()
}

loadCurrent()
</script>

<style scoped>
.mb12 {
	margin-bottom: 12px;
}

.card-title {
	font-weight: 700;
}

.toolbar {
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
}

.pagination-wrap {
	margin-top: 12px;
	display: flex;
	justify-content: flex-end;
}
</style>
