<template>
  <div class="exam-home">
    <header class="home-header">
      <div class="container header-inner">
        <div class="brand" @click="scrollTo('top')">
          <span class="brand-logo">红师</span>
          <div class="brand-meta">
            <strong>红师医学考研中心</strong>
            <small>Medical Postgraduate Entrance Exam</small>
          </div>
        </div>

        <nav class="header-nav">
          <button @click="scrollTo('plan')">备考方案</button>
          <button @click="scrollTo('subjects')">学科模块</button>
          <button @click="scrollTo('service')">督学体系</button>
          <button @click="scrollTo('results')">提分成果</button>
        </nav>

        <div class="header-actions">
          <el-button type="primary" @click="router.push('/login')">登录</el-button>
          <el-button @click="router.push('/register')">注册</el-button>
          <el-button type="danger" plain @click="router.push('/admin/login')">管理员登录</el-button>
        </div>
      </div>
    </header>

    <section id="top" class="hero-wrap">
      <el-carousel
        height="560px"
        trigger="click"
        arrow="always"
        :interval="5000"
        indicator-position="outside"
      >
        <el-carousel-item v-for="item in heroSlides" :key="item.title">
          <article class="hero-slide" :class="`hero-${item.theme}`">
            <div class="overlay"></div>
            <div class="container hero-content">
              <div class="hero-badge">{{ item.badge }}</div>
              <h1>{{ item.title }}</h1>
              <p>{{ item.desc }}</p>
              <div class="hero-tags">
                <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
              </div>
              <div class="hero-buttons">
                <el-button type="primary" size="large" @click="router.push('/register')">免费测评</el-button>
                <el-button size="large" @click="scrollTo('plan')">查看备考路径</el-button>
              </div>
            </div>
          </article>
        </el-carousel-item>
      </el-carousel>
    </section>

    <section class="metrics">
      <div class="container metrics-grid">
        <article class="metric" v-for="item in stats" :key="item.label">
          <div class="metric-value">{{ item.value }}</div>
          <div class="metric-label">{{ item.label }}</div>
        </article>
      </div>
    </section>

    <section id="plan" class="section">
      <div class="container">
        <div class="section-head">
          <h2>全年备考路径</h2>
          <p>围绕医学考研核心科目，按时间轴规划教学重点、训练强度和目标分数区间。</p>
        </div>

        <div class="timeline-grid">
          <article class="timeline-card" v-for="item in planItems" :key="item.stage">
            <div class="timeline-stage">{{ item.stage }}</div>
            <h3>{{ item.title }}</h3>
            <ul>
              <li v-for="point in item.points" :key="point">{{ point }}</li>
            </ul>
          </article>
        </div>
      </div>
    </section>

    <section id="subjects" class="section section-alt">
      <div class="container">
        <div class="section-head">
          <h2>医学考研学科模块</h2>
          <p>西医综合、政治、英语三大模块分层训练，持续复盘错题与易混知识点。</p>
        </div>

        <div class="subject-grid">
          <article class="subject-card" v-for="item in subjectCards" :key="item.title">
            <div class="subject-code">{{ item.code }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
            <div class="subject-list">
              <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section id="service" class="section">
      <div class="container">
        <div class="section-head">
          <h2>督学服务体系</h2>
          <p>从入学诊断到复试前冲刺，形成“计划-执行-反馈-修正”的学习闭环。</p>
        </div>

        <div class="service-grid">
          <article class="service-card" v-for="(item, idx) in serviceItems" :key="item.title">
            <div class="service-no">0{{ idx + 1 }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <section id="results" class="section section-alt">
      <div class="container">
        <div class="section-head">
          <h2>提分成果与训练标准</h2>
          <p>通过周测、月考和模拟卷持续跟踪，保障每位学员都能看到可量化进步。</p>
        </div>

        <div class="result-grid">
          <article class="result-card" v-for="item in resultItems" :key="item.title">
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <section class="final-cta">
      <div class="container cta-panel">
        <h2>你的医学考研冲刺，从一份个性化测评开始</h2>
        <p>填写目标院校与当前基础，生成专属备考建议，匹配课程与督学方案。</p>
        <div class="cta-actions">
          <el-button type="primary" size="large" @click="router.push('/register')">立即预约测评</el-button>
          <el-button size="large" @click="router.push('/login')">已有账号去学习</el-button>
          <el-button type="danger" plain size="large" @click="router.push('/admin/login')">管理后台</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const heroSlides = [
  {
    theme: 'clinical',
    badge: '西医综合专项训练',
    title: '高频病例题深度拆解，建立临床思维与得分路径',
    desc: '覆盖呼吸、循环、消化等核心章节，结合真题出题逻辑训练答题速度与准确率。',
    tags: ['病例分析', '鉴别诊断', '分步作答', '高频错题复盘']
  },
  {
    theme: 'english',
    badge: '考研英语能力提升',
    title: '长难句解析与阅读提速，突破医学考研英语瓶颈',
    desc: '以阅读理解和翻译为核心，强化句法分析、逻辑线索识别和写作表达。',
    tags: ['长难句拆分', '阅读技巧', '翻译训练', '写作模板']
  },
  {
    theme: 'politics',
    badge: '政治冲刺规划',
    title: '选择题刷题 + 主观题框架，后期稳态提分更高效',
    desc: '史纲时间线、马原高频原理、时政热点联动训练，帮助学员快速构建答题框架。',
    tags: ['史纲时间线', '主观题模板', '高频考点', '冲刺复盘']
  },
  {
    theme: 'retest',
    badge: '初复试一体化',
    title: '初试提分与复试准备同步推进，缩短上岸路径',
    desc: '提前布局复试问答、专业表达与面试状态管理，让冲刺阶段更有确定性。',
    tags: ['复试表达', '专业问答', '状态管理', '院校匹配']
  }
]

const stats = [
  { value: '4', label: '全年备考阶段' },
  { value: '12+', label: '核心章节专项' },
  { value: '每周', label: '测评与反馈' },
  { value: '1v1', label: '督学跟进机制' }
]

const planItems = [
  {
    stage: '阶段一 3-6月',
    title: '基础重建',
    points: ['系统梳理西医综合主干知识', '建立章节错题本和知识图谱', '完成入学分层测评并定制计划']
  },
  {
    stage: '阶段二 7-9月',
    title: '专项强化',
    points: ['高频病例题专题训练', '政治英语提分模块并行推进', '周测+月考双轨复盘']
  },
  {
    stage: '阶段三 10-11月',
    title: '真题冲刺',
    points: ['近年真题分题型拆解', '限时训练提升答题节奏', '针对薄弱项进行定向补强']
  },
  {
    stage: '阶段四 12月',
    title: '考前稳态',
    points: ['预测卷与高频考点回看', '考前作息与心态管理', '复试前置准备与答疑']
  }
]

const subjectCards = [
  {
    code: '01',
    title: '西医综合',
    desc: '以内外妇儿和生理病理为主线，聚焦题型规律和病例推理能力。',
    tags: ['内科', '外科', '生理', '病理', '病例题']
  },
  {
    code: '02',
    title: '考研政治',
    desc: '强化选择题稳定得分能力，同时训练主观题材料整合与论述逻辑。',
    tags: ['马原', '史纲', '毛中特', '时政', '主观题']
  },
  {
    code: '03',
    title: '考研英语',
    desc: '围绕阅读、翻译、写作三条主线，建立可迁移的语言解题框架。',
    tags: ['阅读', '翻译', '写作', '词汇', '长难句']
  },
  {
    code: '04',
    title: '复试准备',
    desc: '提前训练专业表达和结构化回答，减少复试阶段突击压力。',
    tags: ['专业问答', '英文表达', '面试礼仪', '院校策略']
  }
]

const serviceItems = [
  { title: '学情诊断', desc: '通过基础测评定位薄弱章节，制定个性化提分目标。' },
  { title: '学习计划', desc: '按周拆解任务与复盘节点，明确每天的执行动作。' },
  { title: '督学跟进', desc: '打卡、作业、模考数据同步跟踪，异常状态及时干预。' },
  { title: '阶段复盘', desc: '每阶段输出学习报告，更新下阶段策略和重点。' }
]

const resultItems = [
  {
    title: '数据化跟踪',
    desc: '每周输出正确率、完成率、耗时分布，帮助学员看到真实进步曲线。'
  },
  {
    title: '薄弱项定位',
    desc: '自动汇总高频错题章节，形成针对性二次训练方案。'
  },
  {
    title: '冲刺节奏控制',
    desc: '考前阶段控制训练强度和复盘节奏，避免无效刷题和过度焦虑。'
  }
]

const scrollTo = (id) => {
  const node = document.getElementById(id)
  if (!node) return
  node.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.exam-home {
  --ink: #112231;
  --soft-ink: #4e6578;
  --line: #d7e2ea;
  --brand: #0d7281;

  min-height: 100vh;
  background:
    radial-gradient(circle at 90% 8%, rgba(42, 141, 169, 0.14) 0%, rgba(42, 141, 169, 0) 34%),
    radial-gradient(circle at 8% 80%, rgba(227, 123, 64, 0.14) 0%, rgba(227, 123, 64, 0) 28%),
    linear-gradient(180deg, #f4f8fc 0%, #f8fbff 100%);
  color: var(--ink);
  font-family: 'Space Grotesk', 'Noto Sans SC', 'PingFang SC', sans-serif;
}

.container {
  width: min(1200px, 92vw);
  margin: 0 auto;
}

.home-header {
  position: sticky;
  top: 0;
  z-index: 40;
  border-bottom: 1px solid rgba(17, 34, 49, 0.08);
  background: rgba(249, 252, 255, 0.9);
  backdrop-filter: blur(9px);
}

.header-inner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  min-height: 78px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.brand-logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #195f8d, #0c887f);
  color: #fff;
  font-weight: 800;
}

.brand-meta {
  display: grid;
  line-height: 1.12;
}

.brand-meta strong {
  font-size: 15px;
}

.brand-meta small {
  color: #6a7f91;
  font-size: 11px;
}

.header-nav {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.header-nav button {
  border: 0;
  background: transparent;
  padding: 7px 10px;
  border-radius: 8px;
  color: #325061;
  cursor: pointer;
  font-weight: 600;
}

.header-nav button:hover {
  background: rgba(13, 114, 129, 0.12);
  color: #0b6773;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.hero-wrap {
  margin-top: 14px;
}

.hero-slide {
  position: relative;
  height: 560px;
  display: grid;
  align-items: center;
  overflow: hidden;
}

.overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(10, 19, 31, 0.62) 0%, rgba(10, 19, 31, 0.18) 62%, rgba(10, 19, 31, 0.08) 100%);
}

.hero-content {
  position: relative;
  z-index: 2;
  color: #fff;
  max-width: 760px;
}

.hero-badge {
  display: inline-flex;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.36);
  background: rgba(255, 255, 255, 0.14);
  padding: 7px 13px;
  font-size: 12px;
  font-weight: 700;
}

.hero-content h1 {
  margin: 14px 0 12px;
  font-size: clamp(32px, 4.8vw, 58px);
  line-height: 1.04;
  letter-spacing: -0.7px;
}

.hero-content p {
  margin: 0;
  line-height: 1.75;
  color: rgba(240, 247, 253, 0.95);
  font-size: 16px;
}

.hero-tags {
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hero-tags span {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.32);
  background: rgba(8, 17, 28, 0.28);
  padding: 5px 10px;
  font-size: 12px;
}

.hero-buttons {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-clinical {
  background:
    radial-gradient(circle at 82% 18%, rgba(134, 238, 255, 0.2) 0%, rgba(134, 238, 255, 0) 36%),
    linear-gradient(130deg, #15395b 0%, #1e6187 52%, #21446d 100%);
}

.hero-english {
  background:
    radial-gradient(circle at 84% 16%, rgba(255, 239, 184, 0.2) 0%, rgba(255, 239, 184, 0) 40%),
    linear-gradient(130deg, #4a3327 0%, #8e5831 50%, #6a3d27 100%);
}

.hero-politics {
  background:
    radial-gradient(circle at 82% 18%, rgba(186, 209, 255, 0.2) 0%, rgba(186, 209, 255, 0) 40%),
    linear-gradient(130deg, #2b3655 0%, #42598d 52%, #334670 100%);
}

.hero-retest {
  background:
    radial-gradient(circle at 82% 16%, rgba(193, 255, 233, 0.2) 0%, rgba(193, 255, 233, 0) 38%),
    linear-gradient(130deg, #15493f 0%, #1d7267 53%, #205247 100%);
}

.metrics {
  margin-top: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(170px, 1fr));
  gap: 12px;
}

.metric {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  padding: 14px;
}

.metric-value {
  font-size: 25px;
  font-weight: 800;
  color: #0e5f7c;
}

.metric-label {
  margin-top: 4px;
  color: #698092;
  font-size: 13px;
}

.section {
  padding: 44px 0;
}

.section-alt {
  background: linear-gradient(180deg, rgba(230, 242, 249, 0.72), rgba(246, 251, 255, 0.55));
}

.section-head h2 {
  margin: 0;
  font-size: clamp(25px, 3vw, 38px);
}

.section-head p {
  margin: 10px 0 0;
  color: var(--soft-ink);
  max-width: 760px;
  line-height: 1.72;
}

.timeline-grid,
.subject-grid,
.service-grid,
.result-grid {
  margin-top: 18px;
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.timeline-card,
.subject-card,
.service-card,
.result-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  padding: 18px;
}

.timeline-stage {
  color: #0b6f7a;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.timeline-card h3,
.subject-card h3,
.service-card h3,
.result-card h3 {
  margin: 10px 0 8px;
}

.timeline-card ul {
  margin: 0;
  padding-left: 18px;
  color: #4d6577;
  line-height: 1.74;
}

.subject-code {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #145a87, #0c7e79);
  color: #fff;
  font-weight: 800;
  font-size: 12px;
}

.subject-card p,
.service-card p,
.result-card p {
  margin: 0;
  color: #4f687a;
  line-height: 1.72;
}

.subject-list {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.subject-list span {
  border-radius: 999px;
  background: #eff6fb;
  border: 1px solid #d2e4f0;
  color: #2f556a;
  padding: 4px 10px;
  font-size: 12px;
}

.service-no {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #11557c, #0d817b);
  color: #fff;
  font-weight: 800;
  font-size: 13px;
}

.final-cta {
  padding: 52px 0 68px;
}

.cta-panel {
  border: 1px solid #d7e2ea;
  border-radius: 20px;
  padding: 30px;
  background:
    radial-gradient(circle at 10% 10%, rgba(132, 219, 234, 0.25) 0%, rgba(132, 219, 234, 0) 36%),
    radial-gradient(circle at 90% 90%, rgba(244, 188, 142, 0.2) 0%, rgba(244, 188, 142, 0) 32%),
    #ffffff;
  text-align: center;
}

.cta-panel h2 {
  margin: 0;
  font-size: clamp(26px, 3vw, 40px);
}

.cta-panel p {
  margin: 10px auto 0;
  color: #4f687a;
  max-width: 760px;
}

.cta-actions {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1080px) {
  .header-inner {
    grid-template-columns: 1fr;
    padding: 10px 0;
  }

  .header-nav {
    justify-content: flex-start;
    overflow-x: auto;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
}

@media (max-width: 760px) {
  .hero-slide {
    height: 500px;
  }

  .hero-content h1 {
    font-size: clamp(28px, 8vw, 42px);
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .cta-panel {
    padding: 22px;
  }
}
</style>
