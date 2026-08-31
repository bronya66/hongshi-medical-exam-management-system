<template>
  <div class="page-shell">

    <el-card class="page-card">
      <template #header>
        <div class="card-title">资料列表</div>
      </template>

      <div class="toolbar-wrap">
        <el-input
          v-model.trim="filter.keyword"
          placeholder="搜索标题/老师/时间"
          clearable
          style="width: 260px"
          @input="currentPage = 1"
        />
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <el-table class="page-table" :data="pagedTableData" border stripe table-layout="auto" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="teacher_name" label="上传老师" width="140" />
        <el-table-column prop="title" label="资料标题" min-width="200" />
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column prop="download_count" label="查看次数" width="120" />
        <el-table-column label="操作" width="190">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewMaterial(row)">查看资料</el-button>
            <el-button v-if="isVideoMaterial(row)" type="success" link @click="openVideo(row)">查看视频</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && filteredTableData.length === 0" description="暂无学习资料" />
      <div class="pagination-wrap" v-if="filteredTableData.length > 0">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="filteredTableData.length"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="videoDialogVisible" :title="videoDialogTitle" width="860px" destroy-on-close @closed="closeVideo">
      <div class="video-wrap">
        <iframe
          v-if="isExternalVideo && videoUrl"
          :src="videoUrl"
          class="video-iframe"
          referrerpolicy="no-referrer"
          allow="autoplay; fullscreen; picture-in-picture"
          allowfullscreen
        />
        <video v-else-if="videoUrl" :src="videoUrl" controls preload="metadata" class="video-player">
          您的浏览器不支持视频播放，请下载后观看。
        </video>
      </div>
      <template #footer>
        <el-button v-if="isExternalVideo && videoUrl" type="primary" link @click="openExternalDirect">新标签打开</el-button>
        <el-button @click="closeVideo">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="materialDialogVisible" :title="materialDialogTitle" width="920px" destroy-on-close @closed="closeMaterial">
      <div class="material-wrap">
        <el-image
          v-if="materialPreviewType === 'image'"
          :src="materialUrl"
          fit="contain"
          class="material-image"
        />
        <iframe
          v-else-if="materialPreviewType === 'iframe'"
          :src="materialUrl"
          class="material-iframe"
          referrerpolicy="no-referrer"
        />
        <el-empty v-else description="当前格式不支持小窗预览，请点击新标签打开" />
      </div>
      <template #footer>
        <el-button type="primary" link @click="openMaterialDirect">新标签打开</el-button>
        <el-button @click="closeMaterial">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 学员资料页面：
// 1. 查看资料列表
// 2. 调用下载接口统计下载次数
// 3. 打开文件地址

import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { downloadMaterialsApi, getStudentMaterialsList } from '../../api/student'

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const videoDialogVisible = ref(false)
const videoUrl = ref('')
const videoDialogTitle = ref('资料视频')
const isExternalVideo = ref(false)
const materialDialogVisible = ref(false)
const materialDialogTitle = ref('资料预览')
const materialUrl = ref('')
const materialPreviewType = ref('unsupported')
const filter = reactive({
  keyword: ''
})

const filteredTableData = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  if (!keyword) return tableData.value
  return tableData.value.filter((item) => {
    const title = String(item.title || '').toLowerCase()
    const teacherName = String(item.teacher_name || '').toLowerCase()
    const uploadTime = String(item.upload_time || '').toLowerCase()
    return title.includes(keyword) || teacherName.includes(keyword) || uploadTime.includes(keyword)
  })
})

const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTableData.value.slice(start, start + pageSize.value)
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getStudentMaterialsList()
    tableData.value = res.data || []
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetFilter = () => {
  filter.keyword = ''
  currentPage.value = 1
}

const VIDEO_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.mov', '.m4v']

const buildUploadUrl = (filePath) => {
  if (!filePath) return ''
  const text = String(filePath).trim().replace(/[。；，、！）】》]+$/g, '')
  if (text.startsWith('http://') || text.startsWith('https://')) return text
  if (text.startsWith('/uploads/')) return text
  return `/uploads/${text}`
}

const isExternalHttpUrl = (url) => {
  if (!url) return false
  if (!(url.startsWith('http://') || url.startsWith('https://'))) return false
  try {
    const parsed = new URL(url)
    return parsed.origin !== window.location.origin
  } catch {
    return true
  }
}

const getFileExtension = (url) => {
  if (!url) return ''
  try {
    const normalized = new URL(url, window.location.origin)
    const path = normalized.pathname || ''
    const idx = path.lastIndexOf('.')
    return idx >= 0 ? path.slice(idx).toLowerCase() : ''
  } catch {
    const clean = String(url).split('?')[0]
    const idx = clean.lastIndexOf('.')
    return idx >= 0 ? clean.slice(idx).toLowerCase() : ''
  }
}

const resolveMaterialPreviewType = (url) => {
  const ext = getFileExtension(url)
  const imageExtSet = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'])
  const iframeExtSet = new Set(['.pdf', '.txt', '.md', '.html', '.htm'])

  if (imageExtSet.has(ext)) return 'image'
  if (iframeExtSet.has(ext)) return 'iframe'
  return 'unsupported'
}

const openInNewTabNoReferrer = (url) => {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.target = '_blank'
  anchor.rel = 'noopener noreferrer'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
}

const isVideoMaterial = (row) => {
  if (String(row?.video_url || '').trim()) return true
  const path = String(row?.file_path || '').toLowerCase()
  return VIDEO_EXTENSIONS.some((ext) => path.endsWith(ext))
}

const openVideo = (row) => {
  const preferredVideoUrl = String(row?.video_url || '').trim()
  const url = preferredVideoUrl ? buildUploadUrl(preferredVideoUrl) : buildUploadUrl(row?.file_path)
  if (!url) {
    ElMessage.warning('当前资料没有可播放的视频文件')
    return
  }

  videoDialogTitle.value = row?.title ? `视频资料：${row.title}` : '资料视频'
  isExternalVideo.value = isExternalHttpUrl(url)
  videoUrl.value = url
  videoDialogVisible.value = true
}

const openExternalDirect = () => {
  if (!videoUrl.value) return
  openInNewTabNoReferrer(videoUrl.value)
}

const closeVideo = () => {
  videoDialogVisible.value = false
  videoUrl.value = ''
  videoDialogTitle.value = '资料视频'
  isExternalVideo.value = false
}

const closeMaterial = () => {
  materialDialogVisible.value = false
  materialDialogTitle.value = '资料预览'
  materialUrl.value = ''
  materialPreviewType.value = 'unsupported'
}

const openMaterialDirect = () => {
  if (!materialUrl.value) return
  openInNewTabNoReferrer(materialUrl.value)
}

const handleViewMaterial = async (row) => {
  const res = await downloadMaterialsApi(row.id)
  const url = res.data?.download_url
  if (url) {
    const builtUrl = buildUploadUrl(url)
    materialDialogTitle.value = row?.title ? `资料预览：${row.title}` : '资料预览'
    materialUrl.value = builtUrl
    materialPreviewType.value = resolveMaterialPreviewType(builtUrl)
    materialDialogVisible.value = true
    ElMessage.success('已打开资料，已统计查看次数')
    loadData()
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-title {
  font-weight: 700;
}

.toolbar-wrap {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.video-wrap {
  background: #000;
  border-radius: 10px;
  overflow: hidden;
}

.video-player {
  width: 100%;
  max-height: 72vh;
  display: block;
}

.video-iframe {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
  background: #000;
}

.material-wrap {
  min-height: 320px;
}

.material-iframe {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
  background: #fff;
}

.material-image {
  width: 100%;
  max-height: 72vh;
}
</style>
