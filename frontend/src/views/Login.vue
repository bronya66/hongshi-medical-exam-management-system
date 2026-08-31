<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="auth-panel">
        <div class="panel-brand">红师医学考研学员管理系统</div>
        <h1>高效协同的备考平台</h1>
        <p>基于角色的服务体验，让学员与老师同频协作。</p>
        <div class="panel-tags">
          <span>角色权限</span>
          <span>数据统计</span>
          <span>全过程记录</span>
        </div>
      </div>
      <el-card class="auth-card" shadow="hover">
        <template #header>
          <div class="title-row">
            <div class="title">系统登录</div>
            <el-button text type="primary" @click="router.push('/')">返回首页</el-button>
          </div>
        </template>

        <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" clearable />
          </el-form-item>

          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
              <el-option label="学员" value="student" />
              <el-option label="任课老师" value="teacher" />
              <el-option label="督学老师" value="supervisor" />
            </el-select>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" @keyup.enter="handleLogin" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="footer-link">
          还没有账号？
          <el-link type="primary" @click="router.push('/register')">去注册</el-link>
          <el-divider direction="vertical" />
          <el-link type="danger" @click="router.push('/admin/login')">管理员登录</el-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
// 登录页：
// 1. 校验账号密码
// 2. 调用 /api/login
// 3. 根据返回角色跳转到对应首页

import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '../api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  role: 'student'
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function getRoleHome(role) {
  if (role === 'student') return '/app/student/dashboard'
  if (role === 'teacher') return '/app/teacher/dashboard'
  if (role === 'supervisor') return '/app/supervisor/dashboard'
  return '/login'
}

const handleLogin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      loading.value = true
      const res = await loginApi({ ...form })

      localStorage.setItem('userInfo', JSON.stringify(res.data || {}))
      ElMessage.success('登录成功')

      router.replace(getRoleHome(res.data.role))
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
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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
