<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="auth-panel">
        <div class="panel-brand">红师医学考研学员管理系统</div>
        <h1>加入学员成长协同网络</h1>
        <p>建立个人档案，连接任课老师与督学，共同完成备考目标。</p>
        <div class="panel-tags">
          <span>档案管理</span>
          <span>资料共享</span>
          <span>督学协作</span>
        </div>
      </div>
      <el-card class="auth-card" shadow="hover">
        <template #header>
          <div class="title-row">
            <div class="title">用户注册</div>
            <el-button text type="primary" @click="router.push('/')">返回首页</el-button>
          </div>
        </template>

        <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" clearable />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入密码" @keyup.enter="handleRegister" />
          </el-form-item>

          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" style="width: 100%" placeholder="请选择角色">
              <el-option label="学员" value="student" />
              <el-option label="任课老师" value="teacher" />
              <el-option label="督学老师" value="supervisor" />
            </el-select>
          </el-form-item>

          <template v-if="form.role === 'student'">
            <el-divider content-position="left">学员补充信息</el-divider>
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
              <el-input-number v-model="form.age" :min="16" :max="60" style="width: 100%" />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model="form.major" placeholder="请输入专业" />
            </el-form-item>
            <el-form-item label="年级">
              <el-input v-model="form.grade" placeholder="请输入年级" />
            </el-form-item>
            <el-form-item label="考研方向" prop="exam_direction">
              <el-select v-model="form.exam_direction" style="width: 100%" placeholder="请选择考研方向（系统将自动分配任课老师）">
                <el-option label="西医临床" value="西医临床" />
                <el-option label="中医临床" value="中医临床" />
                <el-option label="口腔医学" value="口腔医学" />
                <el-option label="其他类（护理学、医学技术、基础医学、公共卫生等）" value="其他类（护理学、医学技术、基础医学、公共卫生等）" />
              </el-select>
            </el-form-item>
            <el-form-item label="班级分配">
              <el-input value="系统将按考研方向自动分配班级" disabled />
            </el-form-item>
          </template>

          <template v-else-if="form.role === 'teacher'">
            <el-divider content-position="left">老师补充信息</el-divider>
            <el-form-item label="老师专业" prop="teacher_major">
              <el-select v-model="form.teacher_major" style="width: 100%" placeholder="请选择老师专业">
                <el-option label="西医临床" value="西医临床" />
                <el-option label="中医临床" value="中医临床" />
                <el-option label="口腔医学" value="口腔医学" />
                <el-option label="其他类（护理学、医学技术、基础医学、公共卫生等）" value="其他类（护理学、医学技术、基础医学、公共卫生等）" />
                <el-option label="政治" value="政治" />
                <el-option label="英语" value="英语" />
              </el-select>
            </el-form-item>
          </template>

          <el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="handleRegister">
              注册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="footer-link">
          已有账号？
          <el-link type="primary" @click="router.push('/login')">去登录</el-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
// 注册页：
// 1. 角色选择（学员/任课老师/督学老师）
// 2. 表单校验
// 3. 学员角色时提交补充信息

import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerApi } from '../api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'student',
  name: '',
  gender: '男',
  age: 22,
  exam_direction: '',
  teacher_major: '',
  major: '',
  grade: ''
})

const validateConfirmPassword = (_, value, callback) => {
  if (!value) {
    callback(new Error('请确认密码'))
  } else if (value !== form.password) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'change' }],
  exam_direction: [{ required: true, message: '请选择考研方向', trigger: 'change' }],
  teacher_major: [{ required: true, message: '请选择老师专业', trigger: 'change' }]
}

const handleRegister = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    const payload = {
      username: form.username,
      password: form.password,
      role: form.role
    }

    if (form.role === 'student') {
      Object.assign(payload, {
        name: form.name,
        gender: form.gender,
        age: form.age,
        exam_direction: form.exam_direction,
        major: form.major,
        grade: form.grade
      })
    } else if (form.role === 'teacher') {
      Object.assign(payload, {
        teacher_major: form.teacher_major
      })
    }

    try {
      loading.value = true
      await registerApi(payload)
      ElMessage.success('注册成功，请登录')
      router.replace('/login')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(140deg, #dfeaff 0%, #f4f7ff 40%, #ffffff 100%);
  padding: 32px 16px;
}

.auth-shell {
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  align-items: stretch;
}

.auth-panel {
  background: linear-gradient(180deg, #0f2f73 0%, #1752ad 80%);
  color: #ffffff;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 20px 40px rgba(15, 47, 115, 0.2);
}

.panel-brand {
  font-weight: 700;
  font-family: 'Space Grotesk', 'Manrope', sans-serif;
  margin-bottom: 12px;
}

.auth-panel h1 {
  margin: 6px 0 10px;
  font-size: 26px;
}

.auth-panel p {
  color: #d7e6ff;
}

.panel-tags {
  display: flex;
  gap: 8px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.panel-tags span {
  background: rgba(255, 255, 255, 0.16);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
}

.auth-card {
  width: 100%;
  border-radius: 18px;
  border: 1px solid #e1e9f7;
  box-shadow: 0 12px 30px rgba(15, 47, 115, 0.12);
}

.title {
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  color: #0f2f73;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-link {
  text-align: center;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
}
</style>
