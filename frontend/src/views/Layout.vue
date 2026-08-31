<template>
  <div class="portal-shell user-portal">
    <div v-if="isMobile && drawerVisible" class="mobile-mask" @click="drawerVisible = false"></div>

    <aside
      class="portal-sidebar"
      :class="{
        collapsed: sidebarCollapsed && !isMobile,
        mobile: isMobile,
        open: drawerVisible
      }"
    >
      <div class="sidebar-brand">
        <div class="brand-mark">HS</div>
        <div v-if="!sidebarCollapsed || isMobile" class="brand-copy">
          <div class="brand-name">红师医学考研</div>
          <div class="brand-sub">Medical Study Hub</div>
        </div>
      </div>

      <el-scrollbar class="sidebar-scroll">
        <section v-for="group in menuGroups" :key="group.title" class="sidebar-group">
          <div v-if="!sidebarCollapsed || isMobile" class="sidebar-group-title">{{ group.title }}</div>
          <button
            v-for="item in group.items"
            :key="item.path"
            type="button"
            class="sidebar-link"
            :class="{ active: activePath === item.path }"
            :title="item.title"
            @click="navigateTo(item.path)"
          >
            <span class="sidebar-link-dot"></span>
            <span v-if="!sidebarCollapsed || isMobile" class="sidebar-link-text">{{ item.title }}</span>
          </button>
        </section>
      </el-scrollbar>
    </aside>

    <div class="portal-main">
      <header class="portal-header">
        <div class="portal-header-left">
          <button v-if="isMobile" type="button" class="header-icon-button" @click="handleMenuToggle">菜单</button>

          <div class="header-brand">
            <span class="header-brand-dot"></span>
            <div>
              <div class="header-brand-title">红师医学考研管理系统</div>
              <div class="header-brand-sub">统一学习服务工作台</div>
            </div>
          </div>

        </div>

        <div class="portal-header-right">
          <div class="notification-wrap" @mouseenter="openNotificationPanel" @mouseleave="closeNotificationPanel">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0">
              <button type="button" class="header-icon-button" @click="toggleNotificationPanel">消息</button>
            </el-badge>
            <div v-if="notificationVisible" class="notification-panel">
              <div class="notification-panel-header">
                <span>通知中心</span>
                <span class="notification-panel-sub">未读 {{ unreadCount }}</span>
              </div>
              <button type="button" v-for="item in notifications" :key="item.id" class="notification-item notification-button" @click="handleNotificationClick(item)">
                <span class="notification-dot" :class="{ unread: !item.is_read }"></span>
                <div class="notification-copy">
                  <div class="notification-title">{{ item.title }}</div>
                  <div class="notification-text">{{ item.content }}</div>
                  <div class="notification-text">{{ item.create_time }}</div>
                </div>
              </button>
              <div v-if="!notifications.length" class="notification-item empty">暂无通知</div>
            </div>
          </div>

          <el-dropdown trigger="hover" @command="handleUserCommand">
            <button class="user-entry" type="button">
              <span class="user-avatar">{{ avatarText }}</span>
              <span class="user-meta">
                <strong>{{ userInfo.username || '未登录用户' }}</strong>
                <small>{{ roleLabel }}</small>
              </span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main ref="mainRef" class="portal-content">
        <section class="content-hero">
          <div>
            <el-breadcrumb separator="/" class="content-breadcrumb">
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item">{{ item }}</el-breadcrumb-item>
            </el-breadcrumb>
            <div class="content-title">{{ currentTitle }}</div>
            <div class="content-subtitle">{{ currentDescription }}</div>
          </div>

          <div class="content-hero-meta">
            <div class="meta-card">
              <span class="meta-label">当前角色</span>
              <strong>{{ roleLabel }}</strong>
            </div>
            <div class="meta-card">
              <span class="meta-label">今日状态</span>
              <strong>{{ todayLabel }}</strong>
            </div>
          </div>
        </section>

        <section class="content-body">
          <router-view />
        </section>
      </main>

      <el-dialog
        v-model="profileDialogVisible"
        title="个人信息"
        width="560px"
        :close-on-click-modal="false"
      >
        <el-form label-width="88px" v-loading="profileLoading">
          <template v-if="userInfo.role === 'student'">
            <el-form-item label="姓名">
              <el-input v-model.trim="profileForm.name" />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="profileForm.gender" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
            <el-form-item label="年龄">
              <el-input-number v-model="profileForm.age" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model.trim="profileForm.major" />
            </el-form-item>
            <el-form-item label="年级">
              <el-input v-model.trim="profileForm.grade" />
            </el-form-item>
            <el-form-item label="班级">
              <el-input v-model.trim="profileForm.class" />
            </el-form-item>
          </template>
          <template v-else-if="userInfo.role === 'teacher'">
            <el-form-item label="姓名">
              <el-input v-model.trim="profileForm.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="profileForm.gender" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model.trim="profileForm.phone" maxlength="11" placeholder="请输入11位手机号" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model.trim="profileForm.email" maxlength="100" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="任教课程">
              <el-select v-model="profileForm.course" placeholder="请选择任教课程" style="width: 100%">
                <el-option
                  v-for="course in teacherCourseOptions"
                  :key="course"
                  :label="course"
                  :value="course"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="个人简介">
              <el-input
                v-model.trim="profileForm.bio"
                type="textarea"
                :rows="3"
                maxlength="500"
                show-word-limit
                placeholder="请简要介绍教学方向与擅长内容"
              />
            </el-form-item>
          </template>
          <el-alert
            v-else
            type="info"
            show-icon
            :closable="false"
            title="当前角色暂无可编辑个人资料字段"
          />
        </el-form>

        <template #footer>
          <el-button @click="profileDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="profileSaving"
            :disabled="!['student', 'teacher'].includes(userInfo.role)"
            @click="handleProfileSave"
          >
            保存
          </el-button>
        </template>
      </el-dialog>

      <footer class="portal-footer">
        <span>红师医学考研管理系统</span>
        <span>Version 2.0 Layout Foundation</span>
      </footer>

      <nav v-if="isMobile" class="mobile-bottom-nav">
        <button
          v-for="item in mobileMenus"
          :key="item.path"
          type="button"
          class="mobile-bottom-link"
          :class="{ active: activePath === item.path }"
          @click="navigateTo(item.path)"
        >
          {{ item.title }}
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { logoutApi } from '../api/auth'
import { getNotificationListApi, markNotificationReadApi } from '../api/notification'
import { getStudentProfileApi, updateStudentProfileApi } from '../api/student'
import { getTeacherProfileApi, updateTeacherProfileApi } from '../api/teacher'
import { isNavigating } from '../utils/navigationState'

const route = useRoute()
const router = useRouter()
const mainRef = ref(null)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
const sidebarCollapsed = ref(false)
const drawerVisible = ref(false)
const notificationVisible = ref(false)
const notifications = ref([])
const profileDialogVisible = ref(false)
const profileLoading = ref(false)
const profileSaving = ref(false)
const profileForm = reactive({
  name: '',
  gender: '男',
  age: 22,
  major: '',
  grade: '',
  class: '',
  course: '',
  phone: '',
  email: '',
  bio: ''
})

const teacherCourseOptions = [
  '西医临床',
  '中医临床',
  '口腔医学',
  '其他类（护理学、医学技术、基础医学、公共卫生等）',
  '政治',
  '英语'
]

const userInfo = computed(() => JSON.parse(localStorage.getItem('userInfo') || '{}'))
const activePath = computed(() => route.path)
const isMobile = computed(() => viewportWidth.value < 768)
const isTablet = computed(() => viewportWidth.value >= 768 && viewportWidth.value < 1200)

const roleLabelMap = {
  student: '学员工作台',
  teacher: '教师工作台',
  supervisor: '督学工作台'
}

const menuGroupMap = {
  student: [
    {
      title: '学习中心',
      items: [
        { title: '学习仪表盘', path: '/app/student/dashboard', description: '查看学习数据与学习进度趋势' },
        { title: '每日打卡', path: '/app/student/checkin', description: '记录学习进度与打卡轨迹' },
        { title: '作业管理', path: '/app/student/homework', description: '查看并提交老师布置的作业' },
        { title: '学习计划', path: '/app/student/learning-plan', description: '拆解目标、管理任务并记录学习进度' },
        { title: '考试中心', path: '/app/student/exam-center', description: '参与模拟考试并查看成绩详情' }
      ]
    },
    {
      title: '资源服务',
      items: [
        { title: '学习资料', path: '/app/student/materials', description: '浏览下载课程学习资料' },
        { title: '资源推荐', path: '/app/student/recommendation', description: '基于学习行为和错题轨迹的个性化资源推荐' },
        { title: '评价老师', path: '/app/student/evaluation', description: '提交课程反馈与教学评价' },
        { title: '通知中心', path: '/app/notifications', description: '统一管理系统与学习提醒通知' }
      ]
    }
  ],
  teacher: [
    {
      title: '教学协同',
      items: [
        { title: '教学仪表盘', path: '/app/teacher/dashboard', description: '查看教学核心数据与评分分布' },
        { title: '学员列表', path: '/app/teacher/student-list', description: '查看当前带教班级学员信息' },
        { title: '发布作业', path: '/app/teacher/publish-homework', description: '发布作业并跟踪提交情况' },
        { title: '上传资料', path: '/app/teacher/upload-materials', description: '维护学习资料与共享资源' },
        { title: '学习计划指导', path: '/app/teacher/learning-plan-guide', description: '查看学员计划概览并批量导入模板' },
        { title: '考试管理', path: '/app/teacher/exam-manage', description: '创建模拟考试并对主观题人工评分' }
      ]
    },
    {
      title: '教学反馈',
      items: [
        { title: '评价列表', path: '/app/teacher/evaluation-list', description: '查看学员对课程的反馈评价' },
        { title: '通知中心', path: '/app/notifications', description: '统一管理系统与教学提醒通知' }
      ]
    }
  ],
  supervisor: [
    {
      title: '督学管理',
      items: [
        { title: '督学仪表盘', path: '/app/supervisor/dashboard', description: '查看打卡率与评价对比数据' },
        { title: '学员管理', path: '/app/supervisor/student-manage', description: '统筹学员基础信息与教学关系' },
        { title: '打卡统计', path: '/app/supervisor/checkin-stat', description: '查看班级打卡统计与趋势' }
      ]
    },
    {
      title: '系统支持',
      items: [
        { title: '通知中心', path: '/app/notifications', description: '统一管理系统通知与督学提醒' }
      ]
    }
  ]
}

function getRoleHome(role) {
  if (role === 'student') return '/app/student/dashboard'
  if (role === 'teacher') return '/app/teacher/dashboard'
  if (role === 'supervisor') return '/app/supervisor/dashboard'
  return '/login'
}

const roleLabel = computed(() => roleLabelMap[userInfo.value.role] || '工作台')
const menuGroups = computed(() => menuGroupMap[userInfo.value.role] || [])
const flatMenus = computed(() => menuGroups.value.flatMap((group) => group.items.map((item) => ({ ...item, group: group.title }))) )
const currentMenu = computed(() => flatMenus.value.find((item) => item.path === activePath.value))
const currentTitle = computed(() => route.meta.title || currentMenu.value?.title || '系统页面')
const currentDescription = computed(() => currentMenu.value?.description || '统一的学习管理与教学协同工作区。')
const breadcrumbs = computed(() => {
  const items = ['工作台首页']
  if (currentMenu.value?.group) items.push(currentMenu.value.group)
  items.push(currentTitle.value)
  return items
})
const unreadCount = computed(() => notifications.value.filter((item) => !item.is_read).length)
const avatarText = computed(() => (userInfo.value.username || 'U').slice(0, 1).toUpperCase())
const mobileMenus = computed(() => flatMenus.value.slice(0, 4))
const todayLabel = computed(() => new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' }))

let notificationPanelCloseTimer = null

const loadNotifications = async () => {
  if (!userInfo.value?.role) return
  const res = await getNotificationListApi()
  notifications.value = (res.data?.list || []).slice(0, 6)
}

const toggleNotificationPanel = async () => {
  notificationVisible.value = !notificationVisible.value
  if (notificationVisible.value) {
    await loadNotifications()
  }
}

const openNotificationPanel = async () => {
  if (notificationPanelCloseTimer) {
    clearTimeout(notificationPanelCloseTimer)
    notificationPanelCloseTimer = null
  }
  if (!notificationVisible.value) {
    notificationVisible.value = true
    await loadNotifications()
  }
}

const closeNotificationPanel = () => {
  if (notificationPanelCloseTimer) {
    clearTimeout(notificationPanelCloseTimer)
  }
  notificationPanelCloseTimer = setTimeout(() => {
    notificationVisible.value = false
  }, 120)
}

const handleNotificationClick = async (item) => {
  if (!item.is_read) {
    await markNotificationReadApi(item.id)
  }
  notificationVisible.value = false
  await loadNotifications()
  if (item.action_path) {
    router.push(item.action_path)
  } else {
    router.push('/app/notifications')
  }
}

const updateViewport = () => {
  viewportWidth.value = window.innerWidth
  if (viewportWidth.value < 768) {
    drawerVisible.value = false
  }
  sidebarCollapsed.value = viewportWidth.value >= 768 && viewportWidth.value < 1200
}

const handleMenuToggle = () => {
  if (isMobile.value) {
    drawerVisible.value = !drawerVisible.value
    return
  }
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const navigateTo = (path) => {
  drawerVisible.value = false
  notificationVisible.value = false
  if (path !== activePath.value) {
    router.push(path).catch(() => {
      router.replace(path).catch(() => {})
    })
  }
}

const openProfileDialog = async () => {
  profileDialogVisible.value = true
  if (!['student', 'teacher'].includes(userInfo.value.role)) {
    return
  }

  profileLoading.value = true
  try {
    if (userInfo.value.role === 'student') {
      const res = await getStudentProfileApi()
      const data = res.data || {}
      profileForm.name = data.name || ''
      profileForm.gender = data.gender || '男'
      profileForm.age = Number(data.age || 22)
      profileForm.major = data.major || ''
      profileForm.grade = data.grade || ''
      profileForm.class = data.class_name || ''
      profileForm.course = ''
      profileForm.phone = ''
      profileForm.email = ''
      profileForm.bio = ''
      return
    }

    const res = await getTeacherProfileApi()
    const data = res.data || {}
    profileForm.name = data.name || ''
    profileForm.gender = data.gender || '男'
    profileForm.course = data.course || ''
    profileForm.phone = data.phone || ''
    profileForm.email = data.email || ''
    profileForm.bio = data.bio || ''
  } finally {
    profileLoading.value = false
  }
}

const handleProfileSave = async () => {
  if (!['student', 'teacher'].includes(userInfo.value.role)) return
  profileSaving.value = true
  try {
    if (userInfo.value.role === 'student') {
      await updateStudentProfileApi({
        name: profileForm.name,
        gender: profileForm.gender,
        age: Number(profileForm.age || 0),
        major: profileForm.major,
        grade: profileForm.grade,
        class: profileForm.class
      })
    } else {
      await updateTeacherProfileApi({
        name: profileForm.name,
        gender: profileForm.gender,
        course: profileForm.course,
        phone: profileForm.phone,
        email: profileForm.email,
        bio: profileForm.bio
      })
    }
    ElMessage.success('个人信息已保存')
    profileDialogVisible.value = false
  } finally {
    profileSaving.value = false
  }
}

const handleUserCommand = async (command) => {
  if (command === 'profile') {
    await openProfileDialog()
    return
  }
  if (command === 'logout') {
    await handleLogout()
  }
}

const handleLogout = async () => {
  try {
    await logoutApi()
  } catch (error) {
    console.warn(error)
  }

  localStorage.removeItem('userInfo')
  ElMessage.success('已退出登录')
  router.replace('/')
}

watch(
  () => route.fullPath,
  async () => {
    notificationVisible.value = false
    await nextTick()
    const mainEl = mainRef.value?.$el || mainRef.value
    if (mainEl) {
      mainEl.scrollTop = 0
    }
    window.scrollTo({ top: 0 })
  },
  { flush: 'post' }
)

onMounted(() => {
  updateViewport()
  window.addEventListener('resize', updateViewport)
  loadNotifications()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateViewport)
  if (notificationPanelCloseTimer) {
    clearTimeout(notificationPanelCloseTimer)
  }
})
</script>

<style scoped>
.portal-shell {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(180deg, #f3f7ff 0%, #f8fbff 55%, #ffffff 100%);
}

.portal-sidebar {
  width: var(--layout-sidebar-width);
  flex: 0 0 var(--layout-sidebar-width);
  background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  transition: width 0.25s ease, transform 0.25s ease;
  z-index: 20;
}

.portal-sidebar.collapsed {
  width: 88px;
  flex-basis: 88px;
}

.portal-sidebar.mobile {
  position: fixed;
  left: 0;
  top: 0;
  transform: translateX(-100%);
  box-shadow: 0 18px 40px rgba(15, 47, 115, 0.16);
}

.portal-sidebar.mobile.open {
  transform: translateX(0);
}

.sidebar-brand {
  height: var(--layout-header-height);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border-color);
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #ffffff;
  background: linear-gradient(135deg, #1890ff, #0f5dd5);
}

.brand-copy {
  min-width: 0;
}

.brand-name {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary);
}

.brand-sub {
  font-size: 11px;
  color: var(--text-tertiary);
}

.sidebar-scroll {
  flex: 1;
}

.sidebar-group {
  padding: 16px 12px 0;
}

.sidebar-group-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-tertiary);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding: 0 10px;
}

.sidebar-link {
  width: 100%;
  border: 0;
  background: transparent;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  color: var(--text-secondary);
  cursor: pointer;
  margin-bottom: 6px;
  transition: all 0.2s ease;
}

.sidebar-link:hover {
  background: #eaf4ff;
  color: var(--primary-color);
}

.sidebar-link.active {
  background: linear-gradient(135deg, #1890ff, #0f68e0);
  color: #ffffff;
  box-shadow: 0 12px 20px rgba(24, 144, 255, 0.22);
}

.sidebar-link-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.88;
  flex: 0 0 auto;
}

.sidebar-link-text {
  font-weight: 700;
  white-space: nowrap;
}

.portal-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.portal-header {
  height: var(--layout-header-height);
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 15;
  gap: 16px;
}

.portal-header-left,
.portal-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.portal-header-left {
  min-width: 0;
  flex: 1;
}

.header-icon-button {
  height: 38px;
  border-radius: 12px;
  border: 1px solid #d9e8fb;
  background: #ffffff;
  color: var(--primary-color);
  padding: 0 14px;
  cursor: pointer;
  font-weight: 700;
  white-space: nowrap;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #0f5dd5);
  box-shadow: 0 0 12px rgba(24, 144, 255, 0.45);
}

.header-brand-title {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary);
}

.header-brand-sub {
  font-size: 11px;
  color: var(--text-tertiary);
}

.notification-wrap {
  position: relative;
}

.notification-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 320px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  box-shadow: 0 20px 40px rgba(15, 47, 115, 0.14);
  padding: 14px;
}

.notification-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 700;
  color: var(--text-primary);
}

.notification-panel-sub {
  font-size: 12px;
  color: var(--text-tertiary);
}

.notification-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid #eff4fb;
}

.notification-button {
  width: 100%;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.notification-item.empty {
  color: var(--text-tertiary);
}

.notification-item:first-of-type {
  border-top: 0;
}

.notification-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d0d9e8;
  margin-top: 6px;
  flex: 0 0 auto;
}

.notification-dot.unread {
  background: var(--primary-color);
  box-shadow: 0 0 0 6px rgba(24, 144, 255, 0.12);
}

.notification-title {
  font-weight: 700;
  color: var(--text-primary);
}

.notification-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.user-entry {
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #1890ff, #0f5dd5);
  color: #ffffff;
  font-weight: 800;
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  color: var(--text-primary);
}

.user-meta small {
  color: var(--text-tertiary);
}

.portal-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.content-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding: 22px 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.18), transparent 28%),
    linear-gradient(135deg, #0c3f97 0%, #125ec9 45%, #2f8df4 100%);
  color: #ffffff;
  box-shadow: 0 18px 32px rgba(18, 94, 201, 0.24);
}

.content-breadcrumb {
  margin-bottom: 10px;
}

.content-breadcrumb :deep(.el-breadcrumb__inner),
.content-breadcrumb :deep(.el-breadcrumb__inner a) {
  color: rgba(255, 255, 255, 0.96);
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(7, 20, 49, 0.28);
}

.content-breadcrumb :deep(.el-breadcrumb__separator) {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(7, 20, 49, 0.24);
}

.content-title {
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
}

.content-subtitle {
  margin-top: 8px;
  max-width: 640px;
  color: rgba(255, 255, 255, 0.88);
}

.content-hero-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.meta-card {
  min-width: 132px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
}

.meta-label {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.82);
  margin-bottom: 6px;
}

.content-body {
  padding-bottom: 10px;
}

.portal-footer {
  height: var(--layout-footer-height);
  border-top: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.mobile-bottom-nav {
  display: none;
}

.mobile-mask {
  position: fixed;
  inset: 0;
  background: rgba(11, 26, 51, 0.35);
  z-index: 19;
}

@media (max-width: 1199px) {
  .header-brand-sub,
  .user-meta small {
    display: none;
  }

  .content-hero {
    flex-direction: column;
  }

  .content-hero-meta {
    justify-content: flex-start;
  }
}

@media (max-width: 767px) {
  .portal-header {
    height: auto;
    min-height: var(--layout-header-height);
    flex-wrap: wrap;
    padding: 10px 14px;
  }

  .portal-header-left,
  .portal-header-right {
    width: 100%;
  }

  .header-brand {
    flex: 1;
  }

  .portal-content {
    padding: 14px;
    padding-bottom: 86px;
  }

  .content-hero {
    border-radius: 20px;
    padding: 18px;
  }

  .content-title {
    font-size: 24px;
  }

  .portal-footer {
    padding-bottom: 50px;
    height: auto;
    min-height: var(--layout-footer-height);
    padding-top: 8px;
  }

  .mobile-bottom-nav {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    height: 56px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    background: rgba(255, 255, 255, 0.96);
    border-top: 1px solid var(--border-color);
    z-index: 18;
  }

  .mobile-bottom-link {
    border: 0;
    background: transparent;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-secondary);
  }

  .mobile-bottom-link.active {
    color: var(--primary-color);
    background: #f2f8ff;
  }

  .notification-panel {
    width: min(320px, calc(100vw - 28px));
    right: -8px;
  }
}
</style>
