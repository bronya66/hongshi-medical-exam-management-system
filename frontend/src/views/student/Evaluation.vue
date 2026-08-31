<template>
  <div class="page-shell">

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">评价任课教师</div>
          </template>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
            <el-form-item label="选择老师" prop="teacher_id">
              <el-select v-model="form.teacher_id" placeholder="请选择任课老师" style="width: 100%" filterable>
                <el-option v-for="item in teacherList" :key="item.id" :label="`${item.username}（ID:${item.id}）`" :value="item.id" />
              </el-select>
            </el-form-item>

            <el-form-item label="评分" prop="score">
              <el-rate v-model="form.score" :max="5" show-score />
            </el-form-item>

            <el-form-item label="评价内容" prop="content">
              <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请输入评价内容" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleSubmit">提交评价</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="page-card">
          <template #header>
            <div class="card-title">我的评价记录</div>
          </template>
          <el-table class="page-table" :data="pagedEvaluationList" border stripe table-layout="auto" v-loading="listLoading">
            <el-table-column prop="teacher_username" label="老师账号" width="140" />
            <el-table-column prop="score" label="评分" width="100" />
            <el-table-column prop="content" label="评价内容" min-width="220" />
            <el-table-column prop="create_time" label="评价时间" width="170" />
            <el-table-column label="操作" width="170">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!listLoading && evaluationList.length === 0" description="暂无评价记录" />
          <div class="pagination-wrap" v-if="evaluationList.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="evaluationList.length"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <el-dialog v-model="dialogVisible" title="编辑评价" width="560px">
    <el-form :model="editForm" label-width="90px">
      <el-form-item label="评分">
        <el-rate v-model="editForm.score" :max="5" show-score />
      </el-form-item>
      <el-form-item label="评价内容">
        <el-input v-model="editForm.content" type="textarea" :rows="4" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
// 学员评价页面：
// 1. 对老师进行评分（1-5 星）
// 2. 填写评价内容
// 3. 调用 /api/student/evaluate_teacher

import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteStudentEvaluationApi,
  evaluateTeacherApi,
  getStudentEvaluationListApi,
  getStudentTeacherListApi,
  updateStudentEvaluationApi
} from '../../api/student'

const formRef = ref(null)
const loading = ref(false)
const teacherList = ref([])
const evaluationList = ref([])
const listLoading = ref(false)
const dialogVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(8)

const editForm = reactive({
  id: null,
  score: 5,
  content: ''
})

const form = reactive({
  teacher_id: null,
  score: 5,
  content: ''
})

const validateScore = (_, value, callback) => {
  if (value < 1 || value > 5) {
    callback(new Error('评分范围必须是 1-5'))
  } else {
    callback()
  }
}

const rules = {
  teacher_id: [{ required: true, message: '请选择老师', trigger: 'change' }],
  score: [{ validator: validateScore, trigger: 'change' }],
  content: [{ required: true, message: '请输入评价内容', trigger: 'blur' }]
}

const pagedEvaluationList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return evaluationList.value.slice(start, start + pageSize.value)
})

const loadTeachers = async () => {
  const res = await getStudentTeacherListApi()
  teacherList.value = res.data || []
}

const loadEvaluationList = async () => {
  try {
    listLoading.value = true
    const res = await getStudentEvaluationListApi()
    evaluationList.value = res.data || []
    currentPage.value = 1
  } finally {
    listLoading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const handleSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      loading.value = true
      await evaluateTeacherApi({ ...form })
      ElMessage.success('评价提交成功')
      form.content = ''
      form.score = 5
      loadEvaluationList()
    } finally {
      loading.value = false
    }
  })
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.score = row.score
  editForm.content = row.content
  dialogVisible.value = true
}

const handleUpdate = async () => {
  await updateStudentEvaluationApi(editForm.id, {
    score: editForm.score,
    content: editForm.content
  })
  ElMessage.success('更新成功')
  dialogVisible.value = false
  loadEvaluationList()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除该评价记录？', '提示', { type: 'warning' })
  await deleteStudentEvaluationApi(row.id)
  ElMessage.success('删除成功')
  loadEvaluationList()
}

onMounted(() => {
  loadTeachers()
  loadEvaluationList()
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
