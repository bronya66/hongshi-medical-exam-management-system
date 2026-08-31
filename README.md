# 红师医学考研管理服务系统

前后端分离的医学考研教务与学习管理系统，包含学员端、任课老师端、督学端与管理员端。

- 前端：Vue 3 + Vite + Vue Router + Element Plus + Axios + ECharts
- 后端：Flask + Flask-Login + Flask-Cors + PyMySQL
- 数据库：MySQL 8+（默认库名 `hongshi_db`）

## 一、项目结构

```text
frontend/
  ├── src/
  │   ├── api/                  # 各角色 API 封装
  │   ├── router/               # 路由守卫与角色路由
  │   ├── views/                # 学员/老师/督学/管理员页面
  │   ├── styles/               # 全局样式
  │   └── utils/                # 前端工具函数
  ├── package.json
  └── vite.config.js

backend/
  ├── app.py                    # Flask 主程序与所有业务接口
  ├── db.py                     # MySQL 连接配置
  ├── schema.sql                # 初始化建表脚本
  ├── scripts/
  │   ├── seed_test_data.py
  │   ├── reset_and_seed_med_exam_data.py
  │   ├── rationalize_test_data.py
  │   └── verify_system_features.py  # 冒烟回归脚本
  └── requirements.txt
```

## 二、核心功能

1. 账号与权限
- 普通用户注册/登录（student、teacher、supervisor）
- 管理员独立登录
- 前端路由守卫 + 后端角色鉴权双保险

2. 基础业务
- 学员端：个人信息、打卡、作业提交、学习资料查看与下载、评价
- 任课老师端：学员管理、作业发布、资料上传、评价查看
- 督学端：学员管理、打卡统计
- 管理端：用户账号、业务数据、运营看板

其中，学员端已实现作业与学习资料的联动管理：作业模块支持查看作业列表、提交作业内容或附件，并保留可追踪的提交记录；资料模块支持查看资料列表、打开资料文件并统计下载次数，便于后续进行学习任务落实和资源热度分析。

3. 进阶模块（已上线）
- 学习计划：计划、任务、学习进度统计
- 复习计划：自动生成复习节奏、复习记录与分析
- 考试模拟：老师创建试卷，学员在线答题与成绩记录
- 资源推荐：基于学习状态的推荐流
- 通知系统：通知持久化、已读状态、业务触发通知（作业/资料/考试）

## 三、环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8+

## 四、数据库初始化

先确保 MySQL 已启动，再在项目根目录执行：

```bash
mysql -uroot -p558000 < backend/schema.sql
```

如需修改数据库连接，请编辑 `backend/db.py`。

## 五、后端启动

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

后端默认地址：`http://localhost:5000`

## 六、前端启动

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://localhost:5173`

Vite 代理已配置：
- `/api` -> `http://localhost:5000`
- `/uploads` -> `http://localhost:5000`

## 七、默认测试账号

后端启动后可使用基础演示账号：

- 学员：张晨 / 123456
- 任课老师：李明 / 123456
- 督学老师：孙华 / 123456
- 管理员：admin / admin123

注：用户密码采用哈希存储。

如执行 `backend/scripts/seed_test_data.py`，会额外生成更多演示账号（含李悦、周凯等）。

## 八、自动化冒烟验证

在后端目录执行：

```bash
python scripts/verify_system_features.py
```

脚本会覆盖多角色核心链路，并输出测试报告到：

- `backend/test_report.md`

## 九、性能优化说明

前端已完成以下优化：

- 路由页面懒加载
- Element Plus 按需引入
- 图表页面动态加载 ECharts
- Vite 手动分包策略优化

目标是减少首屏体积并避免超大 chunk 警告。
