<template>
  <div class="page-shell">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card class="page-card" v-loading="loading">
          <template #header>
            <div class="card-title">推荐线索</div>
          </template>

          <div class="summary-item">复习薄弱任务：{{ summary.weak_review_count || 0 }}</div>
          <div class="summary-item">考试薄弱题目：{{ summary.weak_exam_count || 0 }}</div>
          <div class="summary-item">待完成学习任务：{{ summary.todo_learning_count || 0 }}</div>

          <el-divider />

          <div class="summary-label">关键词画像</div>
          <div class="keyword-wrap">
            <el-tag v-for="kw in keywords" :key="kw" class="keyword-item">{{ kw }}</el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="page-card" v-loading="loading">
          <template #header>
            <div class="header-wrap">
              <div class="card-title">推荐资料</div>
              <el-button @click="loadData">刷新推荐</el-button>
            </div>
          </template>

          <div class="toolbar-wrap">
            <el-input
              v-model.trim="filter.keyword"
              placeholder="搜索标题/老师/推荐原因"
              clearable
              style="width: 280px"
              @input="currentPage = 1"
            />
            <el-button @click="resetFilter">重置</el-button>
          </div>

          <el-table class="page-table" :data="pagedMaterials" border stripe table-layout="auto">
            <el-table-column prop="title" label="资料标题" min-width="220" />
            <el-table-column prop="teacher_name" label="上传老师" width="130" />
            <el-table-column prop="download_count" label="查看量" width="90" />
            <el-table-column prop="reason" label="推荐原因" min-width="160" />
            <el-table-column label="操作" width="190">
              <template #default="{ row }">
                <el-button link type="primary" @click="viewMaterial(row)">查看资料</el-button>
                <el-button v-if="hasVideo(row)" link type="success" @click="viewVideo(row)">查看视频</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && !filteredMaterials.length" description="暂无推荐资料" />
          <div class="pagination-wrap" v-if="filteredMaterials.length > 0">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredMaterials.length"
              @current-change="(page) => (currentPage = page)"
            />
          </div>
        </el-card>

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
              您的浏览器不支持视频播放，请新标签打开观看。
            </video>
          </div>
          <template #footer>
            <el-button v-if="isExternalVideo && videoUrl" type="primary" link @click="openVideoDirect">新标签打开</el-button>
            <el-button @click="closeVideo">关闭</el-button>
          </template>
        </el-dialog>

      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { downloadMaterialsApi, getStudentRecommendationFeedApi } from '../../api/student'

const loading = ref(false)
const keywords = ref([])
const materials = ref([])
const currentPage = ref(1)
const pageSize = ref(8)
const materialDialogVisible = ref(false)
const materialDialogTitle = ref('资料预览')
const materialUrl = ref('')
const materialPreviewType = ref('unsupported')
const videoDialogVisible = ref(false)
const videoDialogTitle = ref('资料视频')
const videoUrl = ref('')
const isExternalVideo = ref(false)
const filter = reactive({
  keyword: ''
})

const VIDEO_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.mov', '.m4v']

const summary = reactive({
  weak_review_count: 0,
  weak_exam_count: 0,
  todo_learning_count: 0
})

const filteredMaterials = computed(() => {
  const keyword = filter.keyword.toLowerCase()
  if (!keyword) return materials.value
  return materials.value.filter((item) => {
    const title = String(item.title || '').toLowerCase()
    const teacherName = String(item.teacher_name || '').toLowerCase()
    const reason = String(item.reason || '').toLowerCase()
    return title.includes(keyword) || teacherName.includes(keyword) || reason.includes(keyword)
  })
})

const pagedMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredMaterials.value.slice(start, start + pageSize.value)
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getStudentRecommendationFeedApi()
    keywords.value = res.data?.keywords || []
    materials.value = res.data?.materials || []

    const s = res.data?.summary || {}
    summary.weak_review_count = s.weak_review_count || 0
    summary.weak_exam_count = s.weak_exam_count || 0
    summary.todo_learning_count = s.todo_learning_count || 0
  } finally {
    loading.value = false
  }
}

const buildUploadUrl = (filePath) => {
  if (!filePath) return ''
  const text = String(filePath).trim().replace(/[。；，、！）】》]+$/g, '')
  if (text.startsWith('http://') || text.startsWith('https://')) return text
  if (text.startsWith('/uploads/')) return text
  return `/uploads/${text}`
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

const resolveMaterialPreviewType = (url) => {
  const ext = getFileExtension(url)
  const imageExtSet = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'])
  const iframeExtSet = new Set(['.pdf', '.txt', '.md', '.html', '.htm'])
  if (imageExtSet.has(ext)) return 'image'
  if (iframeExtSet.has(ext)) return 'iframe'
  return 'unsupported'
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

const hasVideo = (row) => {
  const videoLink = String(row?.video_url || '').trim()
  if (videoLink) return true
  const filePath = String(row?.file_path || '').toLowerCase()
  return VIDEO_EXTENSIONS.some((ext) => filePath.endsWith(ext))
}

const viewVideo = async (row) => {
  let videoSource = String(row?.video_url || '').trim()
  if (!videoSource) {
    const res = await downloadMaterialsApi(row.id)
    videoSource = res.data?.download_url || ''
  }

  const url = buildUploadUrl(videoSource)
  if (!url) {
    ElMessage.warning('当前资料没有可播放的视频文件')
    return
  }

  videoDialogTitle.value = row?.title ? `视频资料：${row.title}` : '资料视频'
  isExternalVideo.value = isExternalHttpUrl(url)
  videoUrl.value = url
  videoDialogVisible.value = true
}

const closeVideo = () => {
  videoDialogVisible.value = false
  videoDialogTitle.value = '资料视频'
  videoUrl.value = ''
  isExternalVideo.value = false
}

const openVideoDirect = () => {
  if (!videoUrl.value) return
  openInNewTabNoReferrer(videoUrl.value)
}

const viewMaterial = async (row) => {
  const res = await downloadMaterialsApi(row.id)
  const url = res.data?.download_url
  if (url) {
    const builtUrl = buildUploadUrl(url)
    materialDialogTitle.value = row?.title ? `资料预览：${row.title}` : '资料预览'
    materialUrl.value = builtUrl
    materialPreviewType.value = resolveMaterialPreviewType(builtUrl)
    materialDialogVisible.value = true
    ElMessage.success('已打开资料，已统计查看次数')
    await loadData()
  }
}

const resetFilter = () => {
  filter.keyword = ''
  currentPage.value = 1
}

loadData()
</script>

<style scoped>
.summary-item {
  margin-bottom: 8px;
  color: var(--text-main);
}

.summary-label {
  margin-bottom: 8px;
  color: var(--text-soft);
  font-size: 13px;
}

.keyword-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-item {
  margin-right: 0;
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

</style>
