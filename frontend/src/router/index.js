// 路由配置（毕设功能全覆盖）
// 关键点：
// 1. 未登录统一跳转登录页
// 2. 已登录按角色访问对应功能页
// 3. 不同角色严格限制可访问菜单与页面

import { createRouter, createWebHistory } from 'vue-router'
import { isNavigating } from '../utils/navigationState'

const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const Home = () => import('../views/Home.vue')
const NotificationCenter = () => import('../views/NotificationCenter.vue')
const Layout = () => import('../views/Layout.vue')
const AdminLogin = () => import('../views/admin/AdminLogin.vue')
const AdminLayout = () => import('../views/admin/AdminLayout.vue')
const AdminDashboard = () => import('../views/admin/AdminDashboard.vue')
const AdminNotifications = () => import('../views/admin/AdminNotifications.vue')
const AdminUsers = () => import('../views/admin/AdminUsers.vue')
const AdminDataOps = () => import('../views/admin/AdminDataOps.vue')
const AdminStudentInfo = () => import('../views/admin/AdminStudentInfo.vue')
const AdminHomework = () => import('../views/admin/AdminHomework.vue')
const AdminMaterials = () => import('../views/admin/AdminMaterials.vue')
const AdminCheckin = () => import('../views/admin/AdminCheckin.vue')
const AdminEvaluation = () => import('../views/admin/AdminEvaluation.vue')
const AdminAccounts = () => import('../views/admin/AdminAccounts.vue')

const StudentInfo = () => import('../views/student/Info.vue')
const StudentDashboard = () => import('../views/student/Dashboard.vue')
const StudentCheckin = () => import('../views/student/Checkin.vue')
const StudentHomework = () => import('../views/student/Homework.vue')
const StudentMaterials = () => import('../views/student/Materials.vue')
const StudentEvaluation = () => import('../views/student/Evaluation.vue')
const StudentLearningPlan = () => import('../views/student/LearningPlan.vue')
const StudentExamCenter = () => import('../views/student/ExamCenter.vue')
const StudentRecommendationCenter = () => import('../views/student/RecommendationCenter.vue')

const TeacherStudentList = () => import('../views/teacher/StudentList.vue')
const TeacherDashboard = () => import('../views/teacher/Dashboard.vue')
const TeacherPublishHomework = () => import('../views/teacher/PublishHomework.vue')
const TeacherUploadMaterials = () => import('../views/teacher/UploadMaterials.vue')
const TeacherEvaluationList = () => import('../views/teacher/EvaluationList.vue')
const TeacherLearningPlanGuide = () => import('../views/teacher/LearningPlanGuide.vue')
const TeacherExamManage = () => import('../views/teacher/ExamManage.vue')

const SupervisorDashboard = () => import('../views/supervisor/Dashboard.vue')
const SupervisorStudentManage = () => import('../views/supervisor/StudentManage.vue')
const SupervisorCheckinStat = () => import('../views/supervisor/CheckinStat.vue')

let prefetched = false

function runWhenIdle(task) {
  if (typeof window !== 'undefined' && typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(task, { timeout: 1200 })
  } else {
    window.setTimeout(task, 600)
  }
}

function prefetchCoreViewsByRole(role) {
  if (prefetched) return
  prefetched = true

  const commonLoaders = [NotificationCenter]
  const roleLoadersMap = {
    student: [StudentDashboard, StudentLearningPlan, StudentExamCenter],
    teacher: [TeacherDashboard, TeacherPublishHomework, TeacherExamManage],
    supervisor: [SupervisorDashboard, SupervisorCheckinStat],
    admin: [AdminDashboard, AdminUsers, AdminDataOps]
  }

  const loaders = [...commonLoaders, ...(roleLoadersMap[role] || [])]
  runWhenIdle(() => {
    Promise.allSettled(loaders.map((loader) => loader())).catch(() => {})
  })
}

function getRoleHome(role) {
  if (role === 'student') return '/app/student/dashboard'
  if (role === 'teacher') return '/app/teacher/dashboard'
  if (role === 'supervisor') return '/app/supervisor/dashboard'
  return '/login'
}

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { title: '系统首页', public: true }
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { title: '登录', public: true }
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: { title: '注册', public: true }
  },
  {
    path: '/admin/login',
    name: 'adminLogin',
    component: AdminLogin,
    meta: { title: '管理员登录', public: true, adminPublic: true }
  },
  {
    path: '/admin',
    component: AdminLayout,
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        component: AdminDashboard,
        meta: { title: '管理员概览', adminOnly: true }
      },
      {
        path: 'notifications',
        component: AdminNotifications,
        meta: { title: '后台通知中心', adminOnly: true }
      },
      {
        path: 'users',
        component: AdminUsers,
        meta: { title: '用户管理', adminOnly: true }
      },
      {
        path: 'student-info',
        component: AdminStudentInfo,
        meta: { title: '学员信息管理', adminOnly: true }
      },
      {
        path: 'homework',
        component: AdminHomework,
        meta: { title: '作业管理', adminOnly: true }
      },
      {
        path: 'materials',
        component: AdminMaterials,
        meta: { title: '学习资料管理', adminOnly: true }
      },
      {
        path: 'checkin',
        component: AdminCheckin,
        meta: { title: '打卡管理', adminOnly: true }
      },
      {
        path: 'evaluation',
        component: AdminEvaluation,
        meta: { title: '评价管理', adminOnly: true }
      },
      {
        path: 'accounts',
        component: AdminAccounts,
        meta: { title: '管理员账号管理', adminOnly: true }
      },
      {
        path: 'data',
        component: AdminDataOps,
        meta: { title: '数据批量操作', adminOnly: true }
      },
    ]
  },
  {
    path: '/app',
    component: Layout,
    redirect: () => {
      const role = JSON.parse(localStorage.getItem('userInfo') || '{}').role
      return getRoleHome(role)
    },
    children: [
      {
        path: 'student/dashboard',
        component: StudentDashboard,
        meta: { title: '学习仪表盘', roles: ['student'] }
      },
      {
        path: 'student/info',
        component: StudentInfo,
        meta: { title: '个人信息', roles: ['student'] }
      },
      {
        path: 'student/checkin',
        component: StudentCheckin,
        meta: { title: '打卡', roles: ['student'] }
      },
      {
        path: 'student/homework',
        component: StudentHomework,
        meta: { title: '作业', roles: ['student'] }
      },
      {
        path: 'student/learning-plan',
        component: StudentLearningPlan,
        meta: { title: '学习计划', roles: ['student'] }
      },
      {
        path: 'student/exam-center',
        component: StudentExamCenter,
        meta: { title: '考试中心', roles: ['student'] }
      },
      {
        path: 'student/materials',
        component: StudentMaterials,
        meta: { title: '学习资料', roles: ['student'] }
      },
      {
        path: 'student/recommendation',
        component: StudentRecommendationCenter,
        meta: { title: '资源推荐', roles: ['student'] }
      },
      {
        path: 'student/evaluation',
        component: StudentEvaluation,
        meta: { title: '评价老师', roles: ['student'] }
      },
      {
        path: 'teacher/dashboard',
        component: TeacherDashboard,
        meta: { title: '教学仪表盘', roles: ['teacher'] }
      },
      {
        path: 'teacher/student-list',
        component: TeacherStudentList,
        meta: { title: '学员列表', roles: ['teacher'] }
      },
      {
        path: 'teacher/publish-homework',
        component: TeacherPublishHomework,
        meta: { title: '发布作业', roles: ['teacher'] }
      },
      {
        path: 'teacher/upload-materials',
        component: TeacherUploadMaterials,
        meta: { title: '上传资料', roles: ['teacher'] }
      },
      {
        path: 'teacher/learning-plan-guide',
        component: TeacherLearningPlanGuide,
        meta: { title: '学习计划指导', roles: ['teacher'] }
      },
      {
        path: 'teacher/exam-manage',
        component: TeacherExamManage,
        meta: { title: '考试管理', roles: ['teacher'] }
      },
      {
        path: 'teacher/evaluation-list',
        component: TeacherEvaluationList,
        meta: { title: '评价列表', roles: ['teacher'] }
      },
      {
        path: 'supervisor/dashboard',
        component: SupervisorDashboard,
        meta: { title: '督学仪表盘', roles: ['supervisor'] }
      },
      {
        path: 'supervisor/student-manage',
        component: SupervisorStudentManage,
        meta: { title: '学员管理', roles: ['supervisor'] }
      },
      {
        path: 'supervisor/checkin-stat',
        component: SupervisorCheckinStat,
        meta: { title: '打卡统计', roles: ['supervisor'] }
      },
      {
        path: 'notifications',
        component: NotificationCenter,
        meta: { title: '通知中心', roles: ['student', 'teacher', 'supervisor'] }
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.fullPath !== from.fullPath) {
    isNavigating.value = true
  }

  const isAdminPath = to.path.startsWith('/admin')
  const adminLoggedIn = !!localStorage.getItem('adminInfo')

  if (isAdminPath) {
    if (to.path === '/admin/login' && adminLoggedIn) {
      next('/admin/dashboard')
      return
    }

    if (to.meta.adminOnly && !adminLoggedIn) {
      next('/admin/login')
      return
    }

    next()
    return
  }

  const isLoggedIn = !!localStorage.getItem('userInfo')
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  const userRole = userInfo.role

  // 未登录且访问的不是公开页 -> 跳转登录页
  if (!isLoggedIn && !to.meta.public) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录访问登录页 -> 回首页
  if (isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next(getRoleHome(userRole))
    return
  }

  // 角色鉴权：如果路由声明了 roles，则需匹配用户角色
  if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    next(getRoleHome(userRole))
    return
  }

  next()
})

router.afterEach((to) => {
  isNavigating.value = false

  const adminInfo = JSON.parse(localStorage.getItem('adminInfo') || '{}')
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  const role = to.path.startsWith('/admin') ? (adminInfo.username ? 'admin' : '') : userInfo.role
  if (role) {
    prefetchCoreViewsByRole(role)
  }

  document.title = to.meta?.title ? `${to.meta.title} - 红师医学考研管理系统` : '红师医学考研管理系统'
})

router.onError(() => {
  isNavigating.value = false
})

export default router
