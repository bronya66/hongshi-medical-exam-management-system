<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="auth-panel">
        <div class="panel-brand">红师医学考研管理后台</div>
        <h1>管理员控制中心</h1>
        <p>统一管理账号、学员数据与教学流程，支持批量维护与导出。</p>
        <div class="panel-tags">
          <span>系统总览</span>
          <span>数据治理</span>
          <span>权限管控</span>
        </div>
      </div>

      <el-card class="auth-card" shadow="hover">
        <template #header>
          <div class="title-row">
            <div class="title">管理员后台登录</div>
            <el-button text type="primary" @click="router.push('/')">返回首页</el-button>
          </div>
        </template>

        <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入管理员账号" clearable />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入管理员密码" @keyup.enter="handleLogin" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
              登录后台
            </el-button>
          </el-form-item>
        </el-form>

        <el-alert class="tips" title="默认管理员：admin / admin123" type="info" :closable="false" show-icon />

        <div class="footer-link">
          普通用户请前往
          <el-link type="primary" @click="router.push('/login')">用户登录</el-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLoginApi } from '../../api/admin'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123'
})

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入管理员密码', trigger: 'blur' }]
}

const handleLogin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      loading.value = true
      const res = await adminLoginApi({ ...form })
      localStorage.setItem('adminInfo', JSON.stringify(res.data || {}))
      ElMessage.success('管理员登录成功')
      router.replace('/admin/dashboard')
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
  background: linear-gradient(150deg, #e7ecf7 0%, #f5f7fb 45%, #ffffff 100%);
  padding: 24px 16px;
}

.auth-shell {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
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
  margin-bottom: 12px;
}

.auth-panel h1 {
  margin: 6px 0 10px;
  font-size: 28px;
}

.auth-panel p {
  color: #d7e6ff;
  line-height: 1.7;
}

.panel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.panel-tags span {
  font-size: 12px;
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.14);
}

.auth-card {
  width: 100%;
  border-radius: 18px;
  border: 1px solid #dbe3f4;
  box-shadow: 0 14px 32px rgba(39, 61, 110, 0.12);
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tips {
  margin-top: 6px;
}

.footer-link {
  margin-top: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  color: #606266;
}

@media (max-width: 768px) {
  .auth-panel {
    padding: 20px;
  }

  .auth-panel h1 {
    font-size: 24px;
  }
}
</style>
