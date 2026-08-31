// Axios 请求封装
// 功能：
// 1. 统一 baseURL
// 2. 响应拦截统一处理后端返回格式：{ code, msg, data }
// 3. code=403 时自动清理登录状态并回到登录页

import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 15000,
  withCredentials: true
})

service.interceptors.request.use(
  (config) => {
    // 当前后端使用 flask-login + session 机制，浏览器会自动携带 Cookie。
    // 此处保留请求拦截便于后续扩展（例如 JWT）。
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    const res = response.data

    // 后端约定：code === 200 为成功
    if (res.code !== 200) {
      ElMessage.error(res.msg || '请求失败')

      // 未登录或无权限时，统一清理状态并返回登录页
      if (res.code === 403) {
        const isAdminPath = window.location.pathname.startsWith('/admin')
        if (isAdminPath) {
          localStorage.removeItem('adminInfo')
          window.location.href = '/admin/login'
        } else {
          localStorage.removeItem('userInfo')
          window.location.href = '/login'
        }
      }

      return Promise.reject(new Error(res.msg || 'Error'))
    }

    return res
  },
  (error) => {
    ElMessage.error(error?.response?.data?.msg || error.message || '网络异常')
    return Promise.reject(error)
  }
)

export default service
