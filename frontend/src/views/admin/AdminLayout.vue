<template>
  <div class="portal-shell admin-portal">
    <div v-if="isMobile && drawerVisible" class="mobile-mask" @click="drawerVisible = false"></div>

    <aside
      class="portal-sidebar admin-sidebar"
      :class="{
        collapsed: sidebarCollapsed && !isMobile,
        mobile: isMobile,
        open: drawerVisible
      }"
    >
      <div class="sidebar-brand admin-brand">
        <div class="brand-mark admin-mark">AD</div>
        <div v-if="!sidebarCollapsed || isMobile" class="brand-copy">
          <div class="brand-name">管理员控制中心</div>
          <div class="brand-sub">Data Governance Console</div>
        </div>
      </div>

      <el-scrollbar class="sidebar-scroll">
        <section v-for="group in menuGroups" :key="group.title" class="sidebar-group">
          <div v-if="!sidebarCollapsed || isMobile" class="sidebar-group-title">{{ group.title }}</div>
          <button
            v-for="item in group.items"
            :key="item.path"
            type="button"
            class="sidebar-link admin-link"
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
      <header class="portal-header admin-header">
        <div class="portal-header-left">
          <button v-if="isMobile" type="button" class="header-icon-button admin-button" @click="handleMenuToggle">菜单</button>

          <div class="header-brand">
            <span class="header-brand-dot admin-dot"></span>
            <div>
              <div class="header-brand-title">后台治理工作台</div>
              <div class="header-brand-sub">账号、教学、学习数据统一管理</div>
            </div>
          </div>

        </div>

        <div class="portal-header-right">
          <div class="notification-wrap" @mouseenter="openNotificationPanel" @mouseleave="closeNotificationPanel">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" type="danger">
              <button type="button" class="header-icon-button admin-button" @click="toggleNotificationPanel">消息</button>
            </el-badge>
            <div v-if="notificationVisible" class="notification-panel">
              <div class="notification-panel-header">
                <span>后台通知</span>
                <span class="notification-panel-sub">待处理 {{ unreadCount }}</span>
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

          <el-dropdown trigger="hover" @command="handleCommand">
            <button class="user-entry" type="button">
              <span class="user-avatar admin-avatar">{{ avatarText }}</span>
              <span class="user-meta">
                <strong>{{ adminInfo.username || 'admin' }}</strong>
                <small>管理员</small>
              </span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="dashboard">数据概览</el-dropdown-item>
                <el-dropdown-item command="notifications">通知中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main ref="mainRef" class="portal-content admin-content">
        <section class="content-hero admin-hero">
          <div>
            <el-breadcrumb separator="/" class="content-breadcrumb">
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item">{{ item }}</el-breadcrumb-item>
            </el-breadcrumb>
            <div class="content-title">{{ currentTitle }}</div>
            <div class="content-subtitle">{{ currentDescription }}</div>
          </div>

          <div class="content-hero-meta">
            <div class="meta-card admin-meta-card">
              <span class="meta-label">当前账号</span>
              <strong>{{ adminInfo.username || 'admin' }}</strong>
            </div>
            <div class="meta-card admin-meta-card">
              <span class="meta-label">后台状态</span>
              <strong>{{ todayLabel }}</strong>
            </div>
          </div>
        </section>

        <section class="content-body">
          <router-view />
        </section>
      </main>

      <footer class="portal-footer admin-footer">
        <span>Medical Admin Console</span>
        <span>Version 2.0 Governance Layout</span>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLogoutApi } from '../../api/admin'
import { getAdminNotificationListApi, markAdminNotificationReadApi } from '../../api/notification'
import { isNavigating } from '../../utils/navigationState'

const route = useRoute()
const router = useRouter()
const mainRef = ref(null)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
const sidebarCollapsed = ref(false)
const drawerVisible = ref(false)
const notificationVisible = ref(false)
const notifications = ref([])
let notificationPanelCloseTimer = null

const adminInfo = computed(() => JSON.parse(localStorage.getItem('adminInfo') || '{}'))
const activePath = computed(() => route.path)
const isMobile = computed(() => viewportWidth.value < 768)

const menuGroups = [
  {
    title: '总览看板',
    items: [
      { title: '数据概览', path: '/admin/dashboard', description: '查看系统核心指标与整体概况' },
      { title: '通知中心', path: '/admin/notifications', description: '查看后台告警与治理提醒通知' }
    ]
  },
  {
    title: '用户治理',
    items: [
      { title: '用户账号', path: '/admin/users', description: '维护普通用户账号与角色' },
      { title: '学员资料', path: '/admin/student-info', description: '维护学员基础档案与师生关系' },
      { title: '管理员账号', path: '/admin/accounts', description: '管理后台管理员登录账号' }
    ]
  },
  {
    title: '教学数据',
    items: [
      { title: '作业管理', path: '/admin/homework', description: '统一巡检平台作业数据' },
      { title: '学习资料', path: '/admin/materials', description: '巡检资料上传与下载记录' },
      { title: '评价管理', path: '/admin/evaluation', description: '查看平台教学评价信息' },
      { title: '打卡管理', path: '/admin/checkin', description: '查看全体学员打卡记录' }
    ]
  },
  {
    title: '系统运维',
    items: [
      { title: '数据批量操作', path: '/admin/data', description: '导出或批量删除业务数据' }
    ]
  }
]

const flatMenus = computed(() => menuGroups.flatMap((group) => group.items.map((item) => ({ ...item, group: group.title }))))
const currentMenu = computed(() => flatMenus.value.find((item) => item.path === activePath.value))
const currentTitle = computed(() => route.meta.title || currentMenu.value?.title || '后台页面')
const currentDescription = computed(() => currentMenu.value?.description || '统一的后台治理与数据巡检工作区。')
const breadcrumbs = computed(() => {
  const items = ['后台首页']
  if (currentMenu.value?.group) items.push(currentMenu.value.group)
  items.push(currentTitle.value)
  return items
})
const unreadCount = computed(() => notifications.value.filter((item) => !item.is_read).length)
const avatarText = computed(() => (adminInfo.value.username || 'A').slice(0, 1).toUpperCase())
const todayLabel = computed(() => new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' }))

const loadNotifications = async () => {
  if (!adminInfo.value?.username) return
  const res = await getAdminNotificationListApi()
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
    await markAdminNotificationReadApi(item.id)
  }
  notificationVisible.value = false
  await loadNotifications()
  if (item.action_path) {
    router.push(item.action_path)
  } else {
    router.push('/admin/notifications')
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

const handleCommand = async (command) => {
  if (command === 'dashboard') {
    navigateTo('/admin/dashboard')
    return
  }
  if (command === 'notifications') {
    navigateTo('/admin/notifications')
    return
  }
  if (command === 'logout') {
    await handleLogout()
  }
}

const handleLogout = async () => {
  try {
    await adminLogoutApi()
  } catch (error) {
    console.warn(error)
  }

  localStorage.removeItem('adminInfo')
  ElMessage.success('已退出管理员后台')
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
  background: linear-gradient(180deg, #f3f5f9 0%, #f7f8fc 48%, #ffffff 100%);
}

.portal-sidebar {
  width: var(--layout-sidebar-width);
  flex: 0 0 var(--layout-sidebar-width);
  background: linear-gradient(180deg, #152038 0%, #10192c 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
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
  box-shadow: 0 20px 44px rgba(11, 19, 36, 0.4);
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #ffffff;
  background: linear-gradient(135deg, #ff6b6b, #f5222d);
}

.brand-name {
  font-size: 14px;
  font-weight: 800;
  color: #ffffff;
}

.brand-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.56);
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
  color: rgba(255, 255, 255, 0.46);
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
  color: rgba(255, 255, 255, 0.76);
  cursor: pointer;
  margin-bottom: 6px;
  transition: all 0.2s ease;
}

.sidebar-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.sidebar-link.active {
  background: linear-gradient(135deg, #f5222d, #ff7875);
  color: #ffffff;
  box-shadow: 0 12px 20px rgba(245, 34, 45, 0.24);
}

.sidebar-link-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
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
  background: rgba(255, 255, 255, 0.94);
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
  border: 1px solid #e1e6f0;
  background: #ffffff;
  color: #39465f;
  padding: 0 14px;
  cursor: pointer;
  font-weight: 700;
  white-space: nowrap;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5222d, #ff9c6e);
  box-shadow: 0 0 12px rgba(245, 34, 45, 0.32);
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
  background: #f5222d;
  box-shadow: 0 0 0 6px rgba(245, 34, 45, 0.12);
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
  background: linear-gradient(135deg, #f5222d, #ff7875);
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
  background: linear-gradient(135deg, #1f2a44 0%, #39465f 55%, #5f6c86 100%);
  color: #ffffff;
  box-shadow: 0 18px 32px rgba(31, 42, 68, 0.2);
}

.content-breadcrumb {
  margin-bottom: 10px;
}

.content-title {
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
}

.content-subtitle {
  margin-top: 8px;
  max-width: 640px;
  color: rgba(255, 255, 255, 0.84);
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
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.meta-label {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 6px;
}

.portal-footer {
  height: var(--layout-footer-height);
  border-top: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.94);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  color: var(--text-tertiary);
  font-size: 12px;
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
  }

  .content-hero {
    border-radius: 20px;
    padding: 18px;
  }

  .content-title {
    font-size: 24px;
  }

  .notification-panel {
    width: min(320px, calc(100vw - 28px));
    right: -8px;
  }
}
</style>

<style scoped>
.app-shell {
  height: 100vh;
  background: #f5f7fb;
  overflow: hidden;
}

.app-shell > .el-container {
  min-height: 0;
}

.app-aside {
  background: linear-gradient(180deg, #1f2a44 0%, #111a2d 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  overflow-y: auto;
}

.app-brand {
  padding: 20px 18px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.app-brand-title {
  color: #ffffff;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.app-brand-sub {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
}

.app-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: rgba(255, 255, 255, 0.82);
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-menu-active-color: #ffffff;
}

:deep(.app-menu .el-menu-item) {
  margin: 6px 10px;
  border-radius: 8px;
}

:deep(.app-menu .el-sub-menu__title) {
  margin: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
}

:deep(.app-menu .el-sub-menu .el-menu-item) {
  margin-left: 18px;
}

:deep(.app-menu .el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.9), rgba(80, 179, 255, 0.9));
  color: #ffffff;
}

.app-header {
  height: 62px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.04);
}

.app-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-username {
  color: #606266;
  font-size: 14px;
}

.app-main {
  padding: 14px 14px 8px;
  background: #f5f7fb;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

:deep(.app-main > .el-card) {
  margin-bottom: 6px;
}

:deep(.app-main .el-card__body) {
  padding-bottom: 10px;
}

:deep(.app-main .pagination-wrap) {
  margin-top: 6px !important;
}

@media (max-width: 1200px) {
  .app-aside {
    width: 210px !important;
  }
}
</style>
