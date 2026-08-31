<template>
  <div class="page-shell">
    <el-card class="page-card">
      <template #header>
        <div class="card-title">学员档案</div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px" class="profile-form" v-loading="loading">
        <el-form-item label="账号">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="form.role" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="form.gender" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄" prop="age">
          <el-input-number v-model="form.age" :min="16" :max="60" />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="form.major" placeholder="请输入专业" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="form.grade" placeholder="请输入年级" />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="form.class" placeholder="请输入班级" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getStudentProfileApi, updateStudentProfileApi } from '../../api/student'

const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)

const form = reactive({
  username: '',
  role: '',
  name: '',
  gender: '男',
  age: 22,
  major: '',
  grade: '',
  class: ''
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'change' }]
}

const roleLabelMap = {
  student: '学员',
  teacher: '教师',
  supervisor: '督学',
  admin: '管理员'
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await getStudentProfileApi()
    const data = res.data || {}
    form.username = data.username || ''
    form.role = roleLabelMap[data.role] || data.role || ''
    form.name = data.name || ''
    form.gender = data.gender || '男'
    form.age = data.age || 22
    form.major = data.major || ''
    form.grade = data.grade || ''
    form.class = data.class_name || ''
  } finally {
    loading.value = false
  }
}

const handleSave = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      saving.value = true
      await updateStudentProfileApi({
        name: form.name,
        gender: form.gender,
        age: form.age,
        major: form.major,
        grade: form.grade,
        class: form.class
      })
      ElMessage.success('保存成功')
      loadData()
    } finally {
      saving.value = false
    }
  })
}

onMounted(loadData)
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.profile-form {
  max-width: 720px;
  margin: 0 auto;
  padding-top: 4px;
}
</style>
