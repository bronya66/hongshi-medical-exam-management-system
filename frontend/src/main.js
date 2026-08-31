// 前端入口文件
// 负责挂载 Vue 应用、路由、Element Plus

import { createApp } from 'vue'
import 'element-plus/dist/index.css'
import { ElLoading } from 'element-plus'
import './styles/navigation.css'

import App from './App.vue'
import router from './router'
import { installSensitiveInputGuard } from './utils/sensitiveFilter'

const app = createApp(App)

app.use(router)
app.directive('loading', ElLoading.directive)
installSensitiveInputGuard()

app.mount('#app')
