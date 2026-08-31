-- =====================================================
-- 红师医学考研学员管理系统（毕设版）数据库初始化 SQL
-- 数据库：MySQL 8+
-- =====================================================

-- 1) 创建数据库
CREATE DATABASE IF NOT EXISTS hongshi_db
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

USE hongshi_db;

-- 2) users 表（用户表：学员/任课老师/督学老师）
-- 字段：id、username、password、role、create_time
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '登录账号（唯一）',
    password VARCHAR(255) NOT NULL COMMENT '登录密码（演示版可明文，生产必须加密）',
    role ENUM('student','teacher','supervisor') NOT NULL COMMENT '角色：student/teacher/supervisor',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB COMMENT='系统用户表';

-- 2.1) admin_users 表（管理员独立账号）
CREATE TABLE IF NOT EXISTS admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '管理员ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员账号',
    password VARCHAR(255) NOT NULL COMMENT '管理员密码哈希',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB COMMENT='管理员账号表';

-- 3) student_info 表（学员信息表）
-- 字段：id、user_id、name、gender、age、major、grade、class、teacher_id
CREATE TABLE IF NOT EXISTS student_info (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学员信息ID',
    user_id INT NOT NULL UNIQUE COMMENT '关联 users.id（学员账号）',
    name VARCHAR(50) NOT NULL COMMENT '学员姓名',
    gender ENUM('male','female','other') DEFAULT 'other' COMMENT '性别',
    age TINYINT UNSIGNED DEFAULT NULL COMMENT '年龄',
    major VARCHAR(100) DEFAULT NULL COMMENT '专业',
    grade VARCHAR(50) DEFAULT NULL COMMENT '年级',
    `class` VARCHAR(50) DEFAULT NULL COMMENT '班级',
    teacher_id INT DEFAULT NULL COMMENT '任课老师ID（users.id）',
    CONSTRAINT fk_student_info_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_student_info_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='学员信息表';

-- 4) homework 表（作业表）
-- 字段：id、teacher_id、title、content、publish_time、deadline
CREATE TABLE IF NOT EXISTS homework (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '作业ID',
    teacher_id INT NOT NULL COMMENT '任课老师ID（users.id）',
    title VARCHAR(200) NOT NULL COMMENT '作业标题',
    content TEXT COMMENT '作业内容',
    file_path VARCHAR(255) DEFAULT NULL COMMENT '作业附件路径（相对 backend/uploads）',
    publish_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    deadline DATETIME NOT NULL COMMENT '截止时间',
    INDEX idx_homework_teacher (teacher_id),
    CONSTRAINT fk_homework_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='作业表';

-- 5) materials 表（学习资料表）
-- 字段：id、teacher_id、title、file_path、upload_time、download_count
CREATE TABLE IF NOT EXISTS materials (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '资料ID',
    teacher_id INT NOT NULL COMMENT '上传老师ID（users.id）',
    title VARCHAR(200) NOT NULL COMMENT '资料标题',
    file_path VARCHAR(255) NOT NULL COMMENT '文件路径（相对 backend/uploads）',
    video_url VARCHAR(2048) DEFAULT NULL COMMENT '视频学习链接（可选）',
    upload_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    download_count INT NOT NULL DEFAULT 0 COMMENT '下载次数',
    INDEX idx_materials_teacher (teacher_id),
    CONSTRAINT fk_materials_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='学习资料表';

-- 6) checkin 表（打卡表）
-- 字段：id、student_id、content、file_path、checkin_date、create_time
CREATE TABLE IF NOT EXISTS checkin (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '打卡ID',
    student_id INT NOT NULL COMMENT '学员ID（users.id）',
    content TEXT COMMENT '打卡内容',
    file_path VARCHAR(255) DEFAULT NULL COMMENT '截图路径（相对 backend/uploads）',
    checkin_date DATE NOT NULL COMMENT '打卡日期',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_student_daily_checkin (student_id, checkin_date),
    INDEX idx_checkin_date (checkin_date),
    CONSTRAINT fk_checkin_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='打卡表（每日限1次）';

-- 7) evaluation 表（评价表）
-- 字段：id、student_id、teacher_id、score、content、create_time
CREATE TABLE IF NOT EXISTS evaluation (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '评价ID',
    student_id INT NOT NULL COMMENT '学员ID（users.id）',
    teacher_id INT NOT NULL COMMENT '老师ID（users.id）',
    score TINYINT NOT NULL COMMENT '评分（1-5星）',
    content TEXT COMMENT '评价内容',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_student_teacher_once (student_id, teacher_id),
    INDEX idx_eval_teacher (teacher_id),
    CONSTRAINT fk_evaluation_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_evaluation_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_eval_score CHECK (score >= 1 AND score <= 5)
) ENGINE=InnoDB COMMENT='评价表（同一学员对同一老师仅1次）';

-- 8) 演示账号由后端启动时自动创建（哈希密码），无需在 SQL 中插入

-- 9) homework_submission 表（作业提交表）
-- 字段：id、homework_id、student_id、content、file_path、score、feedback、submit_time、update_time
CREATE TABLE IF NOT EXISTS homework_submission (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '提交ID',
    homework_id INT NOT NULL COMMENT '作业ID（homework.id）',
    student_id INT NOT NULL COMMENT '学员ID（users.id）',
    content TEXT COMMENT '提交内容',
    file_path VARCHAR(255) DEFAULT NULL COMMENT '附件路径（相对 backend/uploads）',
    score TINYINT DEFAULT NULL COMMENT '老师评分（0-100）',
    feedback TEXT COMMENT '老师评语',
    submit_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_homework_student_once (homework_id, student_id),
    INDEX idx_submission_homework (homework_id),
    INDEX idx_submission_student (student_id),
    CONSTRAINT fk_submission_homework FOREIGN KEY (homework_id) REFERENCES homework(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='作业提交表（同一学员同一作业保留一条提交记录）';

-- 10) learning_plan 表（学习计划表）
CREATE TABLE IF NOT EXISTS learning_plan (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '计划ID',
    student_id INT NOT NULL COMMENT '学员ID（users.id）',
    title VARCHAR(120) NOT NULL COMMENT '计划标题',
    target TEXT COMMENT '学习目标',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    remind_time TIME DEFAULT NULL COMMENT '提醒时间',
    status ENUM('ongoing','completed','paused') NOT NULL DEFAULT 'ongoing' COMMENT '计划状态',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_learning_plan_student (student_id),
    INDEX idx_learning_plan_date (start_date, end_date),
    CONSTRAINT fk_learning_plan_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='学习计划表';

-- 11) learning_task 表（学习任务表）
CREATE TABLE IF NOT EXISTS learning_task (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    plan_id INT NOT NULL COMMENT '计划ID（learning_plan.id）',
    task_title VARCHAR(160) NOT NULL COMMENT '任务标题',
    task_date DATE DEFAULT NULL COMMENT '任务日期',
    estimated_minutes INT DEFAULT NULL COMMENT '预计学习时长（分钟）',
    sort_no INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    is_done TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否完成',
    done_time DATETIME DEFAULT NULL COMMENT '完成时间',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_learning_task_plan (plan_id),
    INDEX idx_learning_task_date (task_date),
    CONSTRAINT fk_learning_task_plan FOREIGN KEY (plan_id) REFERENCES learning_plan(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='学习计划任务表';

-- 12) plan_progress 表（学习进度表）
CREATE TABLE IF NOT EXISTS plan_progress (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '进度ID',
    plan_id INT NOT NULL COMMENT '计划ID（learning_plan.id）',
    progress_date DATE NOT NULL COMMENT '进度日期',
    study_minutes INT NOT NULL DEFAULT 0 COMMENT '学习时长（分钟）',
    note VARCHAR(255) DEFAULT NULL COMMENT '进度备注',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_plan_progress_daily (plan_id, progress_date),
    INDEX idx_plan_progress_date (progress_date),
    CONSTRAINT fk_plan_progress_plan FOREIGN KEY (plan_id) REFERENCES learning_plan(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='学习计划进度表';

-- ==============================
-- 考试模拟模块
-- ==============================
CREATE TABLE IF NOT EXISTS exam (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '考试ID',
    teacher_id INT NOT NULL COMMENT '老师ID（users.id）',
    title VARCHAR(160) NOT NULL COMMENT '考试标题',
    description TEXT COMMENT '考试说明',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME NOT NULL COMMENT '结束时间',
    duration_minutes INT NOT NULL DEFAULT 60 COMMENT '考试时长（分钟）',
    status ENUM('draft','published','closed') NOT NULL DEFAULT 'published' COMMENT '考试状态',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_exam_teacher (teacher_id),
    INDEX idx_exam_time (start_time, end_time),
    CONSTRAINT fk_exam_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='考试表';

CREATE TABLE IF NOT EXISTS question (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '题目ID',
    exam_id INT NOT NULL COMMENT '考试ID（exam.id）',
    question_type ENUM('single','judge','fill','short') NOT NULL COMMENT '题型',
    content TEXT NOT NULL COMMENT '题干',
    options_json TEXT COMMENT '选项JSON（选择题）',
    correct_answer TEXT COMMENT '标准答案',
    analysis TEXT COMMENT '解析',
    score DECIMAL(6,2) NOT NULL DEFAULT 0 COMMENT '题目分值',
    sort_no INT NOT NULL DEFAULT 0 COMMENT '题目序号',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_question_exam (exam_id),
    CONSTRAINT fk_question_exam FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='考试题目表';

CREATE TABLE IF NOT EXISTS question_bank (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '题库题目ID',
    course VARCHAR(100) NOT NULL COMMENT '课程名称',
    section_no INT NOT NULL COMMENT '章节序号',
    section_title VARCHAR(120) NOT NULL COMMENT '章节标题',
    question_type ENUM('single','judge','fill','short') NOT NULL COMMENT '题型',
    content TEXT NOT NULL COMMENT '题干',
    options_json TEXT COMMENT '选择题选项JSON',
    correct_answer TEXT COMMENT '标准答案',
    analysis TEXT COMMENT '解析',
    score DECIMAL(6,2) NOT NULL DEFAULT 0 COMMENT '默认分值',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_question_bank_course_section (course, section_no),
    INDEX idx_question_bank_type (question_type)
) ENGINE=InnoDB COMMENT='考试题库表';

CREATE TABLE IF NOT EXISTS exam_record (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '考试记录ID',
    exam_id INT NOT NULL COMMENT '考试ID（exam.id）',
    student_id INT NOT NULL COMMENT '学员ID（users.id）',
    auto_score DECIMAL(8,2) NOT NULL DEFAULT 0 COMMENT '自动判分',
    manual_score DECIMAL(8,2) NOT NULL DEFAULT 0 COMMENT '手动判分',
    total_score DECIMAL(8,2) NOT NULL DEFAULT 0 COMMENT '总分',
    status ENUM('submitted','reviewed') NOT NULL DEFAULT 'submitted' COMMENT '记录状态',
    submit_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_exam_record_once (exam_id, student_id),
    INDEX idx_exam_record_exam (exam_id),
    INDEX idx_exam_record_student (student_id),
    CONSTRAINT fk_exam_record_exam FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE,
    CONSTRAINT fk_exam_record_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='考试记录表';

CREATE TABLE IF NOT EXISTS answer (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '答案ID',
    record_id INT NOT NULL COMMENT '考试记录ID（exam_record.id）',
    question_id INT NOT NULL COMMENT '题目ID（question.id）',
    answer_text TEXT COMMENT '学员答案',
    is_correct TINYINT(1) DEFAULT NULL COMMENT '是否正确（主观题可为空）',
    score_awarded DECIMAL(8,2) NOT NULL DEFAULT 0 COMMENT '题目得分',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_answer_record_question (record_id, question_id),
    INDEX idx_answer_record (record_id),
    INDEX idx_answer_question (question_id),
    CONSTRAINT fk_answer_record FOREIGN KEY (record_id) REFERENCES exam_record(id) ON DELETE CASCADE,
    CONSTRAINT fk_answer_question FOREIGN KEY (question_id) REFERENCES question(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='考试答案表';

-- ==============================
-- 通知中心模块
-- ==============================
CREATE TABLE IF NOT EXISTS notification (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '通知ID',
    audience_kind ENUM('role','user','admin') NOT NULL COMMENT '通知目标类型',
    target_role ENUM('student','teacher','supervisor') DEFAULT NULL COMMENT '目标角色',
    target_user_id INT DEFAULT NULL COMMENT '目标用户ID（users.id）',
    target_admin_id INT DEFAULT NULL COMMENT '目标管理员ID（admin_users.id）',
    category VARCHAR(32) NOT NULL DEFAULT 'system' COMMENT '通知分类',
    level VARCHAR(16) NOT NULL DEFAULT 'info' COMMENT '通知级别',
    title VARCHAR(180) NOT NULL COMMENT '通知标题',
    content TEXT NOT NULL COMMENT '通知内容',
    action_path VARCHAR(255) DEFAULT NULL COMMENT '跳转路径',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_notification_audience (audience_kind, target_role, target_user_id, target_admin_id),
    INDEX idx_notification_category (category),
    INDEX idx_notification_time (create_time),
    CONSTRAINT fk_notification_target_user FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notification_target_admin FOREIGN KEY (target_admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='通知表';

CREATE TABLE IF NOT EXISTS notification_read (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '已读记录ID',
    notification_id INT NOT NULL COMMENT '通知ID（notification.id）',
    receiver_kind ENUM('user','admin') NOT NULL COMMENT '接收者类型',
    receiver_id INT NOT NULL COMMENT '接收者ID',
    read_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '已读时间',
    UNIQUE KEY uk_notification_read_once (notification_id, receiver_kind, receiver_id),
    INDEX idx_notification_read_receiver (receiver_kind, receiver_id),
    CONSTRAINT fk_notification_read_notification FOREIGN KEY (notification_id) REFERENCES notification(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='通知已读表';
