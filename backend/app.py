"""
红师医学考研学员管理系统 - Flask 后端核心接口（毕设版）

实现内容：
1. 注册 / 登录（基于 flask-login 维护登录态）
2. 角色权限校验（student / teacher / supervisor）
3. 学员信息、作业、资料、打卡、评价全套接口
4. 统一返回结构：{"code":200/400/403, "msg":"", "data":{}}

注意：
- 当前为教学演示版本，密码使用明文比对；生产环境请使用哈希加密（bcrypt/argon2）。
"""

import os
import csv
import time
import uuid
import json
import re
import math
from io import StringIO
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory, session, make_response, g
from flask_cors import CORS
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, insert_and_get_id, query_all, query_one
from utils import ensure_dir, save_upload_file, mask_forbidden_text, first_forbidden_word
from log_utils import init_request_logger, build_request_detail


# ==============================
# Flask 应用初始化
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MATERIALS_DIR = os.path.join(UPLOAD_DIR, "materials")
CHECKIN_DIR = os.path.join(UPLOAD_DIR, "checkin")
HOMEWORK_DIR = os.path.join(UPLOAD_DIR, "homework")

app = Flask(__name__)
app.config["SECRET_KEY"] = "hongshi_graduate_project_secret"
app.config["UPLOAD_DIR"] = UPLOAD_DIR
request_logger = init_request_logger(BASE_DIR)

# 创建上传目录，避免第一次上传报错
ensure_dir(UPLOAD_DIR)
ensure_dir(MATERIALS_DIR)
ensure_dir(CHECKIN_DIR)
ensure_dir(HOMEWORK_DIR)

# 允许前端开发域名跨域访问，并允许携带 Cookie 维持会话
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"]
        }
    },
)


# ==============================
# flask-login 配置
# ==============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None


class User(UserMixin):
    """登录用户对象，挂载角色信息用于权限判断。"""

    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]
        self.role = row["role"]


@login_manager.user_loader
def load_user(user_id):
    """根据用户 ID 加载用户对象。"""
    row = query_one("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    if not row:
        return None
    return User(row)


@login_manager.unauthorized_handler
def unauthorized_handler():
    """未登录统一返回 403。"""
    return api_resp(403, "未登录或登录已过期", {})


# ==============================
# 通用方法
# ==============================
def api_resp(code=200, msg="success", data=None):
    """统一响应格式。"""
    return jsonify({"code": code, "msg": msg, "data": format_response_data(data if data is not None else {})})


def map_gender_to_cn(gender_value):
    if not isinstance(gender_value, str):
        return gender_value
    value = gender_value.strip().lower()
    if value in ["male", "男"]:
        return "男"
    if value in ["female", "女"]:
        return "女"
    if value in ["other", "其他"]:
        return "男"
    return gender_value


def format_response_data(data):
    if isinstance(data, dict):
        formatted = {}
        for key, value in data.items():
            if key == "gender":
                formatted[key] = map_gender_to_cn(value)
            else:
                formatted[key] = format_response_data(value)
        return formatted

    if isinstance(data, (list, tuple)):
        return [format_response_data(item) for item in data]

    if isinstance(data, datetime):
        return data.strftime("%Y年%m月%d日 %H:%M:%S")

    if isinstance(data, date):
        return data.strftime("%Y年%m月%d日")

    if isinstance(data, timedelta):
        total_seconds = int(data.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return data


def role_required(*roles):
    """
    角色权限装饰器。

    用法：
    @login_required
    @role_required('teacher')
    def xxx():
        ...

    核心逻辑：
    - 仅允许指定角色访问
    - 其他角色统一返回 403
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                return api_resp(403, "无权限访问该接口", {})
            return func(*args, **kwargs)

        return wrapper

    return decorator


def handle_errors(error_msg):
    """
    通用异常处理装饰器。
    统一返回 code=400，并记录日志便于排查。
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as error:
                return api_resp(400, str(error), {})
            except Exception:
                app.logger.exception(error_msg)
                return api_resp(500, error_msg, {})

        return wrapper

    return decorator


def parse_json():
    """安全获取 JSON 入参。"""
    return request.get_json(silent=True) or {}


class ValidationError(Exception):
    """业务参数校验异常。"""


def validate_required(payload, field_names):
    """校验必填字段。"""
    missing = []
    for field in field_names:
        value = payload.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
    if missing:
        raise ValidationError(f"缺少必填参数: {', '.join(missing)}")


def validate_role(role):
    if role not in ["student", "teacher", "supervisor"]:
        raise ValidationError("role 非法，仅支持 student/teacher/supervisor")


def validate_username_password(username, password):
    if len(username) < 2 or len(username) > 32:
        raise ValidationError("username 长度需在 2-32 字符")
    if len(password) < 6 or len(password) > 32:
        raise ValidationError("password 长度需在 6-32 字符")


def normalize_gender(gender):
    value = (gender or "male").strip().lower()
    if value in ["male", "男"]:
        return "male"
    if value in ["female", "女"]:
        return "female"
    raise ValidationError("gender 非法，仅支持 男/女（或 male/female）")


def normalize_optional_int(value, field_name, min_value=None, max_value=None):
    if value in [None, ""]:
        return None
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} 必须为整数")

    if min_value is not None and val < min_value:
        raise ValidationError(f"{field_name} 不能小于 {min_value}")
    if max_value is not None and val > max_value:
        raise ValidationError(f"{field_name} 不能大于 {max_value}")
    return val


def normalize_optional_video_url(value):
    text = (value or "").strip()
    text = text.rstrip("。；，、！）】》")
    if not text:
        return None

    if len(text) > 2048:
        raise ValidationError("video_url 长度不能超过 2048 个字符")

    if text.startswith("http://") or text.startswith("https://"):
        return text
    if text.startswith("/uploads/"):
        return text
    if text.startswith("materials/"):
        return f"/uploads/{text}"

    raise ValidationError("video_url 仅支持 http(s) 链接、/uploads/ 开头地址或 materials/ 相对路径")


def normalize_score(score):
    try:
        score_val = int(score)
    except (TypeError, ValueError):
        raise ValidationError("score 必须是 1-5 的整数")
    if score_val < 1 or score_val > 5:
        raise ValidationError("score 取值范围必须为 1-5")
    return score_val


def find_forbidden_in_payload(payload, prefix=""):
    """递归扫描 payload，返回首个命中的字段路径与违规词。"""
    if isinstance(payload, dict):
        for key, value in payload.items():
            current = f"{prefix}.{key}" if prefix else str(key)
            hit = find_forbidden_in_payload(value, current)
            if hit:
                return hit
        return None

    if isinstance(payload, list):
        for idx, item in enumerate(payload):
            current = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            hit = find_forbidden_in_payload(item, current)
            if hit:
                return hit
        return None

    if isinstance(payload, str):
        word = first_forbidden_word(payload)
        if word:
            return prefix or "text", word

    return None


DEADLINE_REMINDER_INTERVAL_SECONDS = 45
_deadline_reminder_last_run = 0.0


@app.before_request
def before_request_logging():
    """记录请求开始时间与上下文。"""
    g.request_start = time.time()
    g.request_id = uuid.uuid4().hex[:8]

    if request.method in {"POST", "PUT", "PATCH"}:
        json_body = request.get_json(silent=True)
        if json_body is not None:
            hit = find_forbidden_in_payload(json_body)
            if hit:
                field, word = hit
                return api_resp(400, f"输入内容包含违规词，请修改后提交（字段: {field}, 词: {word}）", {})

        form_body = request.form.to_dict(flat=True) if request.form else {}
        if form_body:
            hit = find_forbidden_in_payload(form_body)
            if hit:
                field, word = hit
                return api_resp(400, f"输入内容包含违规词，请修改后提交（字段: {field}, 词: {word}）", {})

    try:
        dispatch_deadline_reminders()
    except Exception:
        app.logger.exception("处理截止提醒任务失败")


@app.after_request
def after_request_logging(response):
    """记录请求耗时与结果状态。"""
    latency_ms = int((time.time() - getattr(g, "request_start", time.time())) * 1000)
    user_label = "anonymous"
    if session.get("admin_id"):
        user_label = f"admin:{session.get('admin_username', session.get('admin_id'))}"
    elif current_user.is_authenticated:
        user_label = f"{current_user.role}:{current_user.username}"

    detail = build_request_detail(request.args.to_dict(), request.get_json(silent=True))
    request_logger.info(
        "request completed",
        extra={
            "request_id": getattr(g, "request_id", "-"),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr) or "-",
            "user": user_label,
            "detail": detail,
        },
    )
    return response


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return api_resp(400, str(error), {})


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return api_resp(error.code or 400, error.description or "请求异常", {})


@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    app.logger.exception("未捕获异常: %s", error)
    return api_resp(500, "服务器内部错误，请稍后再试", {})


def is_valid_date(date_text):
    """校验日期字符串格式 YYYY-MM-DD。"""
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def build_next_learning_task_date(base_date):
    """基于给定日期生成下一天的 YYYY-MM-DD 字符串。"""
    if isinstance(base_date, datetime):
        base_date = base_date.date()
    if isinstance(base_date, date):
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    if isinstance(base_date, str) and is_valid_date(base_date):
        parsed_date = datetime.strptime(base_date, "%Y-%m-%d").date()
        return (parsed_date + timedelta(days=1)).strftime("%Y-%m-%d")
    return None


def is_valid_datetime(datetime_text):
    """校验日期时间字符串格式 YYYY-MM-DD HH:MM:SS。"""
    try:
        datetime.strptime(datetime_text, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


def hash_password(password):
    """生成密码哈希。"""
    return generate_password_hash(password)


def verify_password(stored_password, input_password, user_id=None):
    """
    验证明文密码与已存储密码。
    若发现明文密码，则自动升级为哈希存储。
    """
    if stored_password.startswith(("pbkdf2:", "scrypt:", "argon2:")):
        return check_password_hash(stored_password, input_password)

    # 兼容历史明文账号，并在首次登录时自动升级
    if stored_password == input_password and user_id is not None:
        try:
            execute("UPDATE users SET password = %s WHERE id = %s", (hash_password(input_password), user_id))
        except Exception:
            app.logger.exception("自动升级密码哈希失败")
        return True

    return False


def ensure_seed_users():
    """初始化演示账号（若不存在则创建，密码使用哈希存储）。"""
    seed_users = [
        ("张晨", "123456", "student"),
        ("李明", "123456", "teacher"),
        ("孙华", "123456", "supervisor"),
    ]

    for username, raw_password, role in seed_users:
        exists = query_one("SELECT id FROM users WHERE username = %s", (username,))
        if not exists:
            insert_and_get_id(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hash_password(raw_password), role),
            )

    # 自动补充 张晨 的学员信息
    student = query_one("SELECT id FROM users WHERE username = %s", ("张晨",))
    teacher = query_one("SELECT id FROM users WHERE username = %s", ("李明",))
    if student and not query_one("SELECT id FROM student_info WHERE user_id = %s", (student["id"],)):
        insert_and_get_id(
            """
            INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (student["id"], "张晨", "male", 22, "临床医学", "2026", "A班", teacher["id"] if teacher else None),
        )


def ensure_admin_table_and_seed():
    """初始化管理员表和演示管理员账号。"""
    execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '管理员ID',
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员账号',
            password VARCHAR(255) NOT NULL COMMENT '管理员密码哈希',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
        ) ENGINE=InnoDB COMMENT='管理员账号表'
        """
    )

    admin_exists = query_one("SELECT id FROM admin_users WHERE username=%s", ("admin",))
    if not admin_exists:
        insert_and_get_id(
            "INSERT INTO admin_users (username, password) VALUES (%s, %s)",
            ("admin", hash_password("admin123")),
        )


def ensure_homework_submission_table():
    """初始化学员作业提交表。"""
    execute(
        """
        CREATE TABLE IF NOT EXISTS homework_submission (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '提交ID',
            homework_id INT NOT NULL COMMENT '作业ID',
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
        ) ENGINE=InnoDB COMMENT='作业提交表'
        """
    )


def ensure_homework_attachment_column():
    """确保 homework 表存在 file_path 字段（作业附件）。"""
    existed = query_one(
        """
        SELECT 1 AS ok
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'homework'
          AND COLUMN_NAME = 'file_path'
        LIMIT 1
        """
    )
    if not existed:
        execute(
            """
            ALTER TABLE homework
            ADD COLUMN file_path VARCHAR(255) DEFAULT NULL COMMENT '作业附件路径（相对 backend/uploads）' AFTER content
            """
        )


def ensure_materials_video_url_column():
    """确保 materials 表存在 video_url 字段（可选视频学习链接）。"""
    existed = query_one(
        """
        SELECT 1 AS ok
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'materials'
          AND COLUMN_NAME = 'video_url'
        LIMIT 1
        """
    )
    if not existed:
        execute(
            """
            ALTER TABLE materials
            ADD COLUMN video_url VARCHAR(500) DEFAULT NULL COMMENT '视频学习链接（可选）' AFTER file_path
            """
        )


def ensure_materials_video_url_capacity():
    """确保 materials.video_url 字段长度满足长链接存储。"""
    col = query_one(
        """
        SELECT CHARACTER_MAXIMUM_LENGTH AS max_len
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'materials'
          AND COLUMN_NAME = 'video_url'
        LIMIT 1
        """
    )
    if not col:
        return

    max_len = int(col.get("max_len") or 0)
    if max_len < 2048:
        execute(
            """
            ALTER TABLE materials
            MODIFY COLUMN video_url VARCHAR(2048) DEFAULT NULL COMMENT '视频学习链接（可选）'
            """
        )


def ensure_learning_plan_tables():
    """初始化学习计划相关表。"""
    execute(
        """
        CREATE TABLE IF NOT EXISTS learning_plan (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '计划ID',
            student_id INT NOT NULL COMMENT '学员ID（users.id）',
            title VARCHAR(120) NOT NULL COMMENT '计划标题',
            target TEXT COMMENT '学习目标',
            start_date DATE NOT NULL COMMENT '开始日期',
            end_date DATE NOT NULL COMMENT '结束日期',
            remind_time TIME DEFAULT NULL COMMENT '提醒时间',
            status ENUM('ongoing', 'completed', 'paused') NOT NULL DEFAULT 'ongoing' COMMENT '计划状态',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_learning_plan_student (student_id),
            INDEX idx_learning_plan_date (start_date, end_date),
            CONSTRAINT fk_learning_plan_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='学习计划表'
        """
    )

    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='学习计划任务表'
        """
    )

    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='学习计划进度表'
        """
    )


def ensure_exam_tables():
    """初始化考试模拟相关表。"""
    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='考试表'
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS question (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '题目ID',
            exam_id INT NOT NULL COMMENT '考试ID（exam.id）',
            question_type ENUM('single','multi','pair','judge','fill','term','short','essay') NOT NULL COMMENT '题型',
            content TEXT NOT NULL COMMENT '题干',
            options_json TEXT COMMENT '选项JSON（选择题）',
            correct_answer TEXT COMMENT '标准答案',
            analysis TEXT COMMENT '解析',
            score DECIMAL(6,2) NOT NULL DEFAULT 0 COMMENT '题目分值',
            sort_no INT NOT NULL DEFAULT 0 COMMENT '题目序号',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_question_exam (exam_id),
            CONSTRAINT fk_question_exam FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='考试题目表'
        """
    )

    execute(
        """
        ALTER TABLE question
        MODIFY COLUMN question_type ENUM('single','multi','pair','judge','fill','term','short','essay') NOT NULL COMMENT '题型'
        """
    )

    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='考试记录表'
        """
    )

    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='考试答案表'
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS exam_retake_request (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '重考申请ID',
            exam_id INT NOT NULL COMMENT '考试ID（exam.id）',
            student_id INT NOT NULL COMMENT '学员ID（users.id）',
            teacher_id INT NOT NULL COMMENT '老师ID（users.id）',
            reason VARCHAR(500) NOT NULL COMMENT '申请理由',
            status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending' COMMENT '申请状态',
            review_comment VARCHAR(500) DEFAULT NULL COMMENT '老师审核意见',
            review_time DATETIME DEFAULT NULL COMMENT '审核时间',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_retake_exam_student (exam_id, student_id),
            INDEX idx_retake_teacher_status (teacher_id, status),
            INDEX idx_retake_student (student_id),
            CONSTRAINT fk_retake_exam FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE,
            CONSTRAINT fk_retake_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_retake_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='考试重考申请表'
        """
    )


def ensure_notification_tables():
    """初始化通知中心相关表。"""
    execute(
        """
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
        ) ENGINE=InnoDB COMMENT='通知表'
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS notification_read (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '已读记录ID',
            notification_id INT NOT NULL COMMENT '通知ID（notification.id）',
            receiver_kind ENUM('user','admin') NOT NULL COMMENT '接收者类型',
            receiver_id INT NOT NULL COMMENT '接收者ID',
            read_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '已读时间',
            UNIQUE KEY uk_notification_read_once (notification_id, receiver_kind, receiver_id),
            INDEX idx_notification_read_receiver (receiver_kind, receiver_id),
            CONSTRAINT fk_notification_read_notification FOREIGN KEY (notification_id) REFERENCES notification(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='通知已读表'
        """
    )


def create_notification(audience_kind, title, content, category="system", level="info", target_role=None, target_user_id=None, target_admin_id=None, action_path=None):
    """创建一条持久化通知。"""
    if audience_kind not in ["role", "user", "admin"]:
        raise ValidationError("通知 audience_kind 非法")

    # 防刷屏：按业务分类设置合并窗口（秒）。窗口内同目标+同类别+同标题通知合并。
    merge_window_config = {
        "homework": 300,
        "materials": 300,
        "learning_plan": 300,
        "checkin": 600,
        "evaluation": 600,
        "exam": 0,
        "system": 300,
    }
    merge_window_seconds = int(merge_window_config.get(category, 300))
    if merge_window_seconds <= 0:
        return insert_and_get_id(
            """
            INSERT INTO notification (
                audience_kind, target_role, target_user_id, target_admin_id,
                category, level, title, content, action_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (audience_kind, target_role, target_user_id, target_admin_id, category, level, title, content, action_path),
        )

    # 仅合并未被任何人读取的通知，避免覆盖已处理记录。
    cutoff_time = (datetime.now() - timedelta(seconds=merge_window_seconds)).strftime("%Y-%m-%d %H:%M:%S")

    existing = None
    if audience_kind == "role":
        existing = query_one(
            """
            SELECT n.id
            FROM notification n
            WHERE n.audience_kind='role'
              AND n.target_role=%s
              AND n.category=%s
              AND n.title=%s
              AND n.create_time >= %s
              AND NOT EXISTS (
                  SELECT 1 FROM notification_read nr WHERE nr.notification_id = n.id
              )
            ORDER BY n.id DESC
            LIMIT 1
            """,
            (target_role, category, title, cutoff_time),
        )
    elif audience_kind == "user":
        existing = query_one(
            """
            SELECT n.id
            FROM notification n
            WHERE n.audience_kind='user'
              AND n.target_user_id=%s
              AND n.category=%s
              AND n.title=%s
              AND n.create_time >= %s
              AND NOT EXISTS (
                  SELECT 1 FROM notification_read nr WHERE nr.notification_id = n.id
              )
            ORDER BY n.id DESC
            LIMIT 1
            """,
            (target_user_id, category, title, cutoff_time),
        )
    else:
        existing = query_one(
            """
            SELECT n.id
            FROM notification n
            WHERE n.audience_kind='admin'
              AND n.target_admin_id=%s
              AND n.category=%s
              AND n.title=%s
              AND n.create_time >= %s
              AND NOT EXISTS (
                  SELECT 1 FROM notification_read nr WHERE nr.notification_id = n.id
              )
            ORDER BY n.id DESC
            LIMIT 1
            """,
            (target_admin_id, category, title, cutoff_time),
        )

    if existing and existing.get("id"):
        execute(
            """
            UPDATE notification
            SET content=%s, level=%s, action_path=%s, create_time=%s
            WHERE id=%s
            """,
            (content, level, action_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(existing["id"])),
        )
        return int(existing["id"])

    return insert_and_get_id(
        """
        INSERT INTO notification (
            audience_kind, target_role, target_user_id, target_admin_id,
            category, level, title, content, action_path
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (audience_kind, target_role, target_user_id, target_admin_id, category, level, title, content, action_path),
    )


def _notification_exists_for_user(user_id, category, title):
    row = query_one(
        """
        SELECT id FROM notification
        WHERE audience_kind='user' AND target_user_id=%s AND category=%s AND title=%s
        LIMIT 1
        """,
        (int(user_id), category, title),
    )
    return bool(row and row.get("id"))


def _list_students_for_teacher(teacher_id):
    teacher_id = int(teacher_id)
    teacher_course = resolve_teacher_bound_course(teacher_id)
    if teacher_course in ["政治", "英语"]:
        rows = query_all("SELECT user_id FROM student_info")
    else:
        rows = query_all("SELECT user_id FROM student_info WHERE teacher_id=%s", (teacher_id,))
    return [int(item["user_id"]) for item in rows if item.get("user_id")]


def dispatch_deadline_reminders():
    """按固定间隔扫描截止时间并发送前1小时提醒（仅提醒未完成学员）。"""
    global _deadline_reminder_last_run

    now_ts = time.time()
    if now_ts - _deadline_reminder_last_run < DEADLINE_REMINDER_INTERVAL_SECONDS:
        return
    _deadline_reminder_last_run = now_ts

    homework_rows = query_all(
        """
        SELECT id, teacher_id, title, deadline,
               TIMESTAMPDIFF(MINUTE, NOW(), deadline) AS remain_minutes
        FROM homework
        WHERE deadline > NOW()
          AND deadline <= DATE_ADD(NOW(), INTERVAL 60 MINUTE)
        """
    )

    for homework in homework_rows:
        homework_id = int(homework["id"])
        teacher_id = int(homework["teacher_id"])
        remain_minutes = max(1, int(homework.get("remain_minutes") or 1))
        title = f"作业截止提醒：{homework['title']}"

        for student_id in _list_students_for_teacher(teacher_id):
            submitted = query_one(
                "SELECT id FROM homework_submission WHERE homework_id=%s AND student_id=%s",
                (homework_id, student_id),
            )
            if submitted:
                continue

            category = "homework"
            if _notification_exists_for_user(student_id, category, title):
                continue

            create_notification(
                "user",
                title=title,
                content=f"作业预计在约 {remain_minutes} 分钟后截止，请尽快完成并提交。",
                category=category,
                level="warning",
                target_user_id=student_id,
                action_path="/app/student/homework",
            )

    exam_rows = query_all(
        """
        SELECT id, teacher_id, title, end_time,
               TIMESTAMPDIFF(MINUTE, NOW(), end_time) AS remain_minutes
        FROM exam
        WHERE status='published'
          AND end_time > NOW()
          AND end_time <= DATE_ADD(NOW(), INTERVAL 60 MINUTE)
        """
    )

    for exam in exam_rows:
        exam_id = int(exam["id"])
        teacher_id = int(exam["teacher_id"])
        remain_minutes = max(1, int(exam.get("remain_minutes") or 1))
        title = f"考试截止提醒：{exam['title']}"

        for student_id in _list_students_for_teacher(teacher_id):
            submitted = query_one(
                "SELECT id FROM exam_record WHERE exam_id=%s AND student_id=%s",
                (exam_id, student_id),
            )
            if submitted:
                continue

            category = "exam"
            if _notification_exists_for_user(student_id, category, title):
                continue

            create_notification(
                "user",
                title=title,
                content=f"考试预计在约 {remain_minutes} 分钟后截止，请尽快完成作答并提交。",
                category=category,
                level="warning",
                target_user_id=student_id,
                action_path="/app/student/exam",
            )


def mark_notification_read(notification_id, receiver_kind, receiver_id):
    """写入通知已读记录。"""
    exists = query_one(
        "SELECT id FROM notification_read WHERE notification_id=%s AND receiver_kind=%s AND receiver_id=%s",
        (notification_id, receiver_kind, receiver_id),
    )
    if exists:
        return exists["id"]

    return insert_and_get_id(
        """
        INSERT INTO notification_read (notification_id, receiver_kind, receiver_id)
        VALUES (%s, %s, %s)
        """,
        (notification_id, receiver_kind, receiver_id),
    )


def ensure_default_notifications():
    """首次运行写入默认通知，避免通知页空白。"""
    existing = query_one("SELECT COUNT(*) AS total FROM notification")
    if (existing or {}).get("total"):
        return

    create_notification(
        "role",
        title="学习系统升级通知",
        content="统一布局、学习计划、复习计划、考试和推荐模块已上线，可前往工作台体验。",
        category="system",
        level="info",
        target_role="student",
        action_path="/app/student/dashboard",
    )
    create_notification(
        "role",
        title="教学协同升级通知",
        content="学习计划指导、考试管理与推荐能力已开放，请关注学员学习动态。",
        category="system",
        level="info",
        target_role="teacher",
        action_path="/app/teacher/dashboard",
    )
    create_notification(
        "role",
        title="督学巡检升级通知",
        content="系统已新增考试与推荐模块，可结合打卡和学情进行督学巡检。",
        category="system",
        level="info",
        target_role="supervisor",
        action_path="/app/supervisor/dashboard",
    )
    create_notification(
        "admin",
        title="后台通知中心已启用",
        content="通知中心已接入真实持久化数据，可查看业务告警与系统提醒。",
        category="system",
        level="warning",
        action_path="/admin/notifications",
    )


def get_user_notification_list(user_id, role, category=None):
    """获取普通用户通知列表。"""
    conditions = ["(n.audience_kind='user' AND n.target_user_id=%s)", "(n.audience_kind='role' AND n.target_role=%s)"]
    params = [user_id, role]
    if category and category != "all":
        conditions.append("n.category=%s")
        params.append(category)

    where_sql = "(" + " OR ".join(conditions[:2]) + ")"
    if category and category != "all":
        where_sql += " AND n.category=%s"

    return query_all(
        f"""
        SELECT n.id, n.category, n.level, n.title, n.content, n.action_path, n.create_time,
               CASE WHEN nr.id IS NULL THEN 0 ELSE 1 END AS is_read
        FROM notification n
        LEFT JOIN notification_read nr
               ON nr.notification_id = n.id AND nr.receiver_kind='user' AND nr.receiver_id=%s
        WHERE {where_sql}
        ORDER BY n.create_time DESC, n.id DESC
        """,
        (user_id, *params),
    )


def get_admin_notification_list(admin_id, category=None):
    """获取管理员通知列表。"""
    where_sql = "(n.audience_kind='admin' AND (n.target_admin_id IS NULL OR n.target_admin_id=%s))"
    params = [admin_id]
    if category and category != "all":
        where_sql += " AND n.category=%s"
        params.append(category)

    return query_all(
        f"""
        SELECT n.id, n.category, n.level, n.title, n.content, n.action_path, n.create_time,
               CASE WHEN nr.id IS NULL THEN 0 ELSE 1 END AS is_read
        FROM notification n
        LEFT JOIN notification_read nr
               ON nr.notification_id = n.id AND nr.receiver_kind='admin' AND nr.receiver_id=%s
        WHERE {where_sql}
        ORDER BY n.create_time DESC, n.id DESC
        """,
        (admin_id, *params),
    )


def migrate_gender_to_cn():
    """历史数据迁移：兼容中文值并统一到英文枚举（仅 male/female）。"""
    execute("UPDATE student_info SET gender='male' WHERE gender='男'")
    execute("UPDATE student_info SET gender='female' WHERE gender='女'")
    execute("UPDATE student_info SET gender='male' WHERE gender='其他'")
    execute("UPDATE student_info SET gender='male' WHERE LOWER(gender)='other'")


def admin_required(func):
    """管理员接口鉴权：要求 session 中存在 admin_id。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        admin_id = session.get("admin_id")
        if not admin_id:
            return api_resp(403, "管理员未登录或登录已过期", {})
        return func(*args, **kwargs)

    return wrapper


def build_csv_response(filename, rows, header_order):
    """将列表数据导出为 CSV 下载响应。"""
    stream = StringIO()
    stream.write("\ufeff")
    writer = csv.writer(stream)
    writer.writerow(header_order)
    for item in rows:
        writer.writerow([item.get(col, "") for col in header_order])

    output = make_response(stream.getvalue())
    output.headers["Content-Type"] = "text/csv; charset=utf-8"
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return output


# 初始化演示账号（哈希密码），用于项目演示
try:
    ensure_seed_users()
except Exception:
    app.logger.exception("初始化演示账号失败，可能是数据库连接异常")

try:
    ensure_admin_table_and_seed()
except Exception:
    app.logger.exception("初始化管理员账号失败，可能是数据库连接异常")

try:
    ensure_homework_submission_table()
except Exception:
    app.logger.exception("初始化作业提交表失败，可能是数据库连接异常")

try:
    ensure_homework_attachment_column()
except Exception:
    app.logger.exception("初始化作业附件字段失败，可能是数据库连接异常")

try:
    ensure_materials_video_url_column()
except Exception:
    app.logger.exception("初始化资料视频链接字段失败，可能是数据库连接异常")

try:
    ensure_materials_video_url_capacity()
except Exception:
    app.logger.exception("扩容资料视频链接字段失败，可能是数据库连接异常")

try:
    ensure_learning_plan_tables()
except Exception:
    app.logger.exception("初始化学习计划表失败，可能是数据库连接异常")

try:
    ensure_exam_tables()
except Exception:
    app.logger.exception("初始化考试表失败，可能是数据库连接异常")

try:
    ensure_notification_tables()
except Exception:
    app.logger.exception("初始化通知表失败，可能是数据库连接异常")

try:
    ensure_default_notifications()
except Exception:
    app.logger.exception("初始化默认通知失败，可能是数据库连接异常")

try:
    migrate_gender_to_cn()
except Exception:
    app.logger.exception("迁移性别字段为中文失败，可能是数据库连接异常")


# ==============================
# 认证接口
# ==============================
def normalize_exam_direction(value):
    text = (value or "").strip()
    allowed = {
        "西医临床",
        "中医临床",
        "口腔医学",
        "其他类（护理学、医学技术、基础医学、公共卫生等）",
        "政治",
        "英语",
    }
    return text if text in allowed else ""


def infer_exam_direction_from_major(major):
    text = (major or "").strip()
    if not text:
        return ""

    if any(k in text for k in ["西医", "临床", "内科", "外科"]):
        return "西医临床"
    if any(k in text for k in ["中医", "针灸", "中西医"]):
        return "中医临床"
    if any(k in text for k in ["口腔", "牙"]):
        return "口腔医学"
    if any(k in text for k in ["护理", "公卫", "公共卫生", "医学技术", "基础医学"]):
        return "其他类（护理学、医学技术、基础医学、公共卫生等）"
    return ""


def resolve_teacher_id_by_exam_direction(exam_direction):
    row = query_one(
        """
        SELECT u.id
        FROM teacher_course_binding tcb
        JOIN users u ON u.id = tcb.teacher_id
        WHERE u.role='teacher' AND tcb.course=%s
        ORDER BY u.id ASC
        LIMIT 1
        """,
        (exam_direction,),
    )
    if row and row.get("id"):
        return int(row["id"])

    fallback_map = {
        "西医临床": "李明",
        "中医临床": "周凯",
        "口腔医学": "陈洁",
        "其他类（护理学、医学技术、基础医学、公共卫生等）": "刘颖",
        "政治": "王雪",
        "英语": "赵宁",
    }
    fallback_username = fallback_map.get(exam_direction)
    if not fallback_username:
        return None

    teacher = query_one(
        "SELECT id FROM users WHERE role='teacher' AND username=%s LIMIT 1",
        (fallback_username,),
    )
    return int(teacher["id"]) if teacher and teacher.get("id") else None


def build_auto_class_name(exam_direction, grade):
    """按方向自动分班：优先填充未满班，满员后新开班。"""
    direction_label_map = {
        "西医临床": "临床医学",
        "中医临床": "中医临床",
        "口腔医学": "口腔医学",
        "其他类（护理学、医学技术、基础医学、公共卫生等）": "医护公卫",
    }
    direction_label = direction_label_map.get(exam_direction, "考研综合")

    class_prefix = f"{direction_label}"
    class_capacity = 40

    rows = query_all(
        """
        SELECT s.`class` AS class_name, COUNT(*) AS total
        FROM student_info s
        JOIN teacher_course_binding tcb ON tcb.teacher_id = s.teacher_id
        WHERE tcb.course=%s
          AND s.`class` LIKE %s
        GROUP BY s.`class`
        """,
                (exam_direction, f"{class_prefix}%"),
    )

    parsed = []
    for row in rows:
        class_name = str(row.get("class_name") or "")
        match = re.match(rf"^{re.escape(class_prefix)}(\d+)班$", class_name)
        if not match:
            continue
        parsed.append(
            {
                "index": int(match.group(1)),
                "class_name": class_name,
                "total": int(row.get("total") or 0),
            }
        )

    if parsed:
        parsed.sort(key=lambda x: (x["total"], x["index"]))
        if parsed[0]["total"] < class_capacity:
            return parsed[0]["class_name"]

        max_index = max(item["index"] for item in parsed)
        return f"{class_prefix}{max_index + 1}班"

    return f"{class_prefix}1班"


@app.post("/api/register")
@handle_errors("数据库操作失败")
def register():
    """
    注册接口：
    1) 创建 users 记录
    2) 若角色为 student，自动创建 student_info 记录

    入参示例：
    {
      "username": "stu1001",
      "password": "123456",
        "role": "student|teacher|supervisor",
        "name": "张三",
        "gender": "男",
        "age": 22,
        "exam_direction": "西医临床",
        "teacher_major": "西医临床",
        "major": "临床医学",
        "grade": "2026"
    }
    """
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "").strip()

    validate_required(payload, ["username", "password", "role"])
    validate_role(role)
    validate_username_password(username, password)

    exists = query_one("SELECT id FROM users WHERE username = %s", (username,))
    if exists:
        return api_resp(400, "用户名已存在", {})

    user_id = insert_and_get_id(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, hash_password(password), role),
    )

    # 学员注册时，自动创建 student_info 记录
    if role == "student":
        name = (payload.get("name") or username).strip()
        gender = normalize_gender(payload.get("gender"))
        age = normalize_optional_int(payload.get("age"), "age", min_value=10, max_value=80)
        exam_direction = normalize_exam_direction(payload.get("exam_direction"))
        major = (payload.get("major") or "").strip() or None
        grade = (payload.get("grade") or "").strip() or None

        if not exam_direction:
            exam_direction = infer_exam_direction_from_major(major)
        if not exam_direction:
            return api_resp(400, "请先选择考研方向，再进行注册", {})
        if exam_direction in ["政治", "英语"]:
            return api_resp(400, "学员考研方向不包含政治/英语，请按专业方向选择", {})

        class_name = build_auto_class_name(exam_direction, grade)

        teacher_id = resolve_teacher_id_by_exam_direction(exam_direction)
        if teacher_id is None:
            return api_resp(400, f"当前考研方向【{exam_direction}】暂未配置任课老师，请联系管理员", {})

        insert_and_get_id(
            """
            INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, name, gender, age, major, grade, class_name, teacher_id),
        )

    if role == "teacher":
        teacher_major = normalize_exam_direction(payload.get("teacher_major"))
        if not teacher_major:
            return api_resp(400, "请先选择老师专业", {})

        execute(
            """
            INSERT INTO teacher_course_binding (teacher_id, course)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE course=VALUES(course)
            """,
            (int(user_id), teacher_major),
        )

    return api_resp(200, "注册成功", {"user_id": user_id})


@app.post("/api/login")
@handle_errors("数据库操作失败")
def login():
    """
    登录接口：
    - 校验账号密码
    - 使用 flask-login 维护会话态
    - 返回角色信息
    """
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "").strip()

    validate_required(payload, ["username", "password"])
    validate_username_password(username, password)
    if role:
        validate_role(role)

    if role:
        row = query_one(
            "SELECT id, username, password, role FROM users WHERE username = %s AND role=%s",
            (username, role),
        )
    else:
        row = query_one(
            "SELECT id, username, password, role FROM users WHERE username = %s",
            (username,),
        )
    if not row or not verify_password(row["password"], password, row["id"]):
        return api_resp(400, "用户名或密码错误", {})

    login_user(User(row))

    return api_resp(
        200,
        "登录成功",
        {
            "user_id": row["id"],
            "username": row["username"],
            "role": row["role"],
        },
    )


@app.post("/api/logout")
@login_required
@handle_errors("数据库操作失败")
def logout():
    """退出登录。"""
    logout_user()
    return api_resp(200, "退出成功", {})


@app.get("/api/public/teacher_list")
@handle_errors("数据库操作失败")
def public_teacher_list():
    """注册页公开获取任课老师账号列表。"""
    rows = query_all("SELECT id, username FROM users WHERE role='teacher' ORDER BY id DESC")
    return api_resp(200, "查询成功", rows)


# ==============================
# 学员信息接口
# ==============================
@app.get("/api/supervisor/student_list")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_student_list():
    """
    督学老师查询学员信息。
    支持按姓名和班级筛选。
    """
    name = (request.args.get("name") or "").strip()
    class_name = (request.args.get("class") or "").strip()

    conditions = ["u.role = 'student'"]
    params = []

    if name:
        conditions.append("s.name LIKE %s")
        params.append(f"%{name}%")

    if class_name:
        conditions.append("s.`class` = %s")
        params.append(class_name)

    where_sql = " AND ".join(conditions)
    sql = f"""
        SELECT
            s.id,
            s.user_id,
            s.name,
            s.gender,
            s.age,
            s.major,
            s.grade,
            s.`class` AS class_name,
            s.teacher_id,
            t.username AS teacher_username
        FROM student_info s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN users t ON s.teacher_id = t.id
        WHERE {where_sql}
        ORDER BY s.id DESC
    """
    rows = query_all(sql, params)
    return api_resp(200, "查询成功", rows)


@app.post("/api/supervisor/edit_student")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_edit_student():
    """
    督学老师编辑学员信息。
    可编辑字段：name/gender/age/major/grade/class/teacher_id
    """
    payload = parse_json()
    student_id = payload.get("id")

    if not student_id:
        return api_resp(400, "缺少学员ID", {})

    student = query_one("SELECT id FROM student_info WHERE id = %s", (student_id,))
    if not student:
        return api_resp(400, "学员记录不存在", {})

    teacher_id = payload.get("teacher_id")
    if teacher_id is not None:
        teacher = query_one("SELECT id, role FROM users WHERE id = %s", (teacher_id,))
        if not teacher or teacher["role"] != "teacher":
            return api_resp(400, "teacher_id 不存在或不是任课老师", {})

    execute(
        """
        UPDATE student_info
        SET name=%s, gender=%s, age=%s, major=%s, grade=%s, `class`=%s, teacher_id=%s
        WHERE id=%s
        """,
        (
            (payload.get("name") or "").strip() or "未命名",
            normalize_gender(payload.get("gender")),
            payload.get("age"),
            (payload.get("major") or "").strip() or None,
            (payload.get("grade") or "").strip() or None,
            (payload.get("class") or "").strip() or None,
            teacher_id,
            student_id,
        ),
    )

    return api_resp(200, "编辑成功", {})


@app.delete("/api/supervisor/student/<int:student_info_id>")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_delete_student(student_info_id):
    """督学老师删除学员档案。"""
    existing = query_one("SELECT id FROM student_info WHERE id=%s", (student_info_id,))
    if not existing:
        return api_resp(400, "学员档案不存在", {})

    execute("DELETE FROM student_info WHERE id=%s", (student_info_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/teacher/student_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_student_list():
    """
    任课老师查询学员列表。
    - 政治/英语属于公共课，默认展示全体学员；
    - 其他课程仍按 teacher_id 仅展示名下学员。
    """
    teacher_id = int(current_user.id)
    bound_course = resolve_teacher_bound_course(teacher_id)
    is_public_course = bound_course in ["政治", "英语"]

    if is_public_course:
        sql = """
        SELECT
            s.id,
            s.user_id,
            s.name,
            s.gender,
            s.age,
            s.major,
            s.grade,
            s.`class` AS class_name,
            s.teacher_id
        FROM student_info s
        ORDER BY s.id DESC
        """
        rows = query_all(sql)
    else:
        sql = """
        SELECT
            s.id,
            s.user_id,
            s.name,
            s.gender,
            s.age,
            s.major,
            s.grade,
            s.`class` AS class_name,
            s.teacher_id
        FROM student_info s
        WHERE s.teacher_id = %s
        ORDER BY s.id DESC
        """
        rows = query_all(sql, (teacher_id,))

    return api_resp(200, "查询成功", rows)


@app.get("/api/student/profile")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_profile_get():
    """学员查看个人信息。"""
    row = query_one(
        """
        SELECT s.id, s.user_id, u.username, u.role,
               s.name, s.gender, s.age, s.major, s.grade, s.`class` AS class_name, s.teacher_id
        FROM student_info s
        JOIN users u ON u.id = s.user_id
        WHERE s.user_id = %s
        """,
        (int(current_user.id),),
    )
    if not row:
        return api_resp(400, "未找到学员档案", {})
    return api_resp(200, "查询成功", row)


@app.put("/api/student/profile")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_profile_update():
    """学员编辑个人信息。"""
    payload = parse_json()
    profile = query_one("SELECT id FROM student_info WHERE user_id = %s", (int(current_user.id),))
    if not profile:
        return api_resp(400, "未找到学员档案", {})

    name = (payload.get("name") or "").strip() or current_user.username
    gender = normalize_gender(payload.get("gender"))
    age = normalize_optional_int(payload.get("age"), "age", min_value=10, max_value=80)
    major = (payload.get("major") or "").strip() or None
    grade = (payload.get("grade") or "").strip() or None
    class_name = (payload.get("class") or "").strip() or None

    execute(
        """
        UPDATE student_info
        SET name=%s, gender=%s, age=%s, major=%s, grade=%s, `class`=%s
        WHERE user_id=%s
        """,
        (
            name,
            gender,
            age,
            major,
            grade,
            class_name,
            int(current_user.id),
        ),
    )
    return api_resp(200, "保存成功", {})


@app.get("/api/teacher/profile")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_profile_get():
    """老师查看个人信息。"""
    # 防御性初始化，避免部署后因表未建导致接口直接报“数据库操作失败”
    ensure_teacher_course_binding_table()
    ensure_teacher_profile_table()
    ensure_teacher_profile_columns()

    row = query_one(
        """
        SELECT
            u.id AS user_id,
            u.username,
            u.role,
            tcb.course,
            tp.name,
            tp.gender,
            tp.phone,
            tp.email,
            COALESCE(tp.bio, tp.intro) AS bio
        FROM users u
        LEFT JOIN teacher_course_binding tcb ON tcb.teacher_id = u.id
        LEFT JOIN teacher_profile tp ON tp.teacher_id = u.id
        WHERE u.id = %s
        LIMIT 1
        """,
        (int(current_user.id),),
    )
    if not row:
        return api_resp(400, "未找到老师档案", {})

    row["name"] = (row.get("name") or row.get("username") or "").strip()
    row["gender"] = normalize_gender(row.get("gender"))
    row["phone"] = (row.get("phone") or "").strip()
    row["email"] = (row.get("email") or "").strip()
    row["bio"] = (row.get("bio") or "").strip()
    return api_resp(200, "查询成功", row)


@app.put("/api/teacher/profile")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_profile_update():
    """老师编辑个人信息。"""
    # 防御性初始化，避免部署后首次保存时表缺失
    ensure_teacher_course_binding_table()
    ensure_teacher_profile_table()
    ensure_teacher_profile_columns()

    payload = parse_json()
    course = normalize_exam_direction(payload.get("course"))
    name = (payload.get("name") or "").strip() or current_user.username
    gender = normalize_gender(payload.get("gender"))
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()
    bio = (payload.get("bio") or "").strip()

    if not course:
        return api_resp(400, "course 非法，请选择有效任教课程", {})
    if len(name) > 50:
        return api_resp(400, "name 长度不能超过 50", {})
    if phone and len(phone) > 20:
        return api_resp(400, "phone 长度不能超过 20", {})
    if email and len(email) > 100:
        return api_resp(400, "email 长度不能超过 100", {})
    if bio and len(bio) > 500:
        return api_resp(400, "bio 长度不能超过 500", {})
    if phone and not re.fullmatch(r"\d{11}", phone):
        return api_resp(400, "phone 格式错误，请输入 11 位手机号", {})
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return api_resp(400, "email 格式错误", {})

    execute(
        """
        INSERT INTO teacher_course_binding (teacher_id, course)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE course=VALUES(course)
        """,
        (int(current_user.id), course),
    )

    execute(
        """
        INSERT INTO teacher_profile (teacher_id, name, gender, phone, email, bio, intro)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name),
            gender=VALUES(gender),
            phone=VALUES(phone),
            email=VALUES(email),
            bio=VALUES(bio),
            intro=VALUES(intro)
        """,
        (
            int(current_user.id),
            name,
            gender,
            phone or None,
            email or None,
            bio or None,
            bio or None,
        ),
    )
    return api_resp(200, "保存成功", {})


@app.get("/api/student/checkin_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_checkin_list():
    """学员查看自己的打卡记录。"""
    rows = query_all(
        """
        SELECT id, student_id, content, file_path, checkin_date, create_time
        FROM checkin
        WHERE student_id=%s
        ORDER BY checkin_date DESC, id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


def get_student_related_teacher_ids(student_user_id):
    """获取学员已建立关联的老师 ID 列表，用于过滤无关课程内容。"""
    related_ids = set()

    profile = query_one(
        "SELECT teacher_id, major FROM student_info WHERE user_id=%s LIMIT 1",
        (int(student_user_id),),
    )
    if profile and profile.get("teacher_id"):
        related_ids.add(int(profile["teacher_id"]))

    major_direction = infer_exam_direction_from_major((profile or {}).get("major"))
    if major_direction:
        major_teacher_id = resolve_teacher_id_by_exam_direction(major_direction)
        if major_teacher_id:
            related_ids.add(int(major_teacher_id))

    # 政治、英语是必考公共课，默认加入关联老师列表。
    public_course_rows = query_all(
        """
        SELECT teacher_id
        FROM teacher_course_binding
        WHERE course IN ('政治', '英语')
        """,
    )
    related_ids.update(int(row["teacher_id"]) for row in public_course_rows if row.get("teacher_id"))

    evaluation_rows = query_all(
        "SELECT DISTINCT teacher_id FROM evaluation WHERE student_id=%s AND teacher_id IS NOT NULL",
        (int(student_user_id),),
    )
    related_ids.update(int(row["teacher_id"]) for row in evaluation_rows if row.get("teacher_id"))

    exam_rows = query_all(
        """
        SELECT DISTINCT e.teacher_id
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        WHERE er.student_id=%s AND e.teacher_id IS NOT NULL
        """,
        (int(student_user_id),),
    )
    related_ids.update(int(row["teacher_id"]) for row in exam_rows if row.get("teacher_id"))

    submission_rows = query_all(
        """
        SELECT DISTINCT h.teacher_id
        FROM homework_submission hs
        JOIN homework h ON h.id = hs.homework_id
        WHERE hs.student_id=%s AND h.teacher_id IS NOT NULL
        """,
        (int(student_user_id),),
    )
    related_ids.update(int(row["teacher_id"]) for row in submission_rows if row.get("teacher_id"))

    return sorted(related_ids)


def get_student_evaluation_teacher_ids(student_user_id):
    """获取学员可评价老师（仅专业课+政治+英语）。"""
    related_ids = []

    profile = query_one(
        "SELECT teacher_id, major FROM student_info WHERE user_id=%s LIMIT 1",
        (int(student_user_id),),
    )

    # 专业课老师：优先 student_info.teacher_id，其次按方向绑定推断。
    major_teacher_id = None
    if profile and profile.get("teacher_id"):
        major_teacher_id = int(profile["teacher_id"])
    else:
        major_direction = infer_exam_direction_from_major((profile or {}).get("major"))
        if major_direction:
            major_teacher_id = resolve_teacher_id_by_exam_direction(major_direction)

    if major_teacher_id:
        related_ids.append(int(major_teacher_id))

    # 公共课固定保留政治、英语各一位老师（按 teacher_id 升序取首位）。
    for course_name in ["政治", "英语"]:
        row = query_one(
            """
            SELECT teacher_id
            FROM teacher_course_binding
            WHERE course=%s AND teacher_id IS NOT NULL
            ORDER BY teacher_id ASC
            LIMIT 1
            """,
            (course_name,),
        )
        if row and row.get("teacher_id"):
            teacher_id = int(row["teacher_id"])
            if teacher_id not in related_ids:
                related_ids.append(teacher_id)

    return related_ids


def get_student_profile_and_primary_teacher(student_user_id):
    """获取学员展示名及其主带教老师ID（student_info.teacher_id）。"""
    row = query_one(
        """
        SELECT s.teacher_id,
               COALESCE(s.name, u.username) AS student_name,
               u.username AS student_username
        FROM users u
        LEFT JOIN student_info s ON s.user_id = u.id
        WHERE u.id=%s
        LIMIT 1
        """,
        (int(student_user_id),),
    )
    return row or {"teacher_id": None, "student_name": current_user.username, "student_username": current_user.username}


def infer_learning_task_course(task_title):
    """根据任务标题粗略识别所属课程，用于老师端学习指导展示过滤。"""
    text = str(task_title or "").strip()
    if not text:
        return ""

    course_keywords = {
        "英语": ["英语", "词汇", "阅读", "翻译", "写作", "完形", "语法"],
        "政治": ["政治", "马原", "毛概", "思修", "时政", "主观题"],
        "西医临床": ["西医", "临床", "内科", "外科", "诊断", "病例", "生理", "病理", "药理"],
        "中医临床": ["中医", "辨证", "方剂", "中药", "针灸", "经络", "伤寒"],
        "口腔医学": ["口腔", "牙体", "牙周", "修复", "正畸", "颌面"],
        "其他类（护理学、医学技术、基础医学、公共卫生等）": ["护理", "公卫", "流行病", "医学技术", "基础医学"],
    }

    for course, keywords in course_keywords.items():
        if any(keyword in text for keyword in keywords):
            return course
    return ""


def is_learning_task_visible_for_teacher(task_title, teacher_course):
    """判断任务是否应展示给当前课程老师。"""
    if not teacher_course:
        return True

    if teacher_course in ["政治", "英语"]:
        return True

    task_course = infer_learning_task_course(task_title)
    if not task_course:
        return False
    return task_course == teacher_course


def normalize_task_title_by_teacher_course(task_title, teacher_course):
    """将老师下发任务标题规范到其绑定课程下。"""
    normalized = str(task_title or "").strip()
    if not normalized:
        return normalized

    if not teacher_course or teacher_course in ["政治", "英语"]:
        return normalized

    inferred_course = infer_learning_task_course(normalized)
    if inferred_course and inferred_course != teacher_course:
        raise ValidationError(f"当前老师课程为 {teacher_course}，任务标题与课程不匹配")

    if not inferred_course:
        return f"{teacher_course}：{normalized}"
    return normalized


def infer_learning_plan_course(plan_title, plan_target):
    """根据学习计划标题/目标识别课程。"""
    text = f"{plan_title or ''} {plan_target or ''}".strip()
    if not text:
        return ""
    return infer_learning_task_course(text)


@app.get("/api/student/teacher_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_teacher_list():
    """学员获取可评价的老师列表。"""
    related_teacher_ids = get_student_evaluation_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(200, "查询成功", [])

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    rows = query_all(
        f"SELECT id, username FROM users WHERE role='teacher' AND id IN ({placeholders}) ORDER BY id DESC",
        tuple(related_teacher_ids),
    )
    return api_resp(200, "查询成功", rows)


# ==============================
# 学习计划接口
# ==============================
@app.get("/api/student/learning_plan_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_plan_list():
    """学员查看自己的学习计划列表（含任务完成统计）。"""
    rows = query_all(
        """
     SELECT lp.id, lp.student_id, lp.title, lp.target, lp.start_date, lp.end_date,
         lp.remind_time, lp.status, lp.create_time, lp.update_time,
         COALESCE(task_stat.task_total, 0) AS task_total,
         COALESCE(task_stat.task_done, 0) AS task_done,
         COALESCE(progress_stat.total_minutes, 0) AS total_minutes
        FROM learning_plan lp
     LEFT JOIN (
         SELECT plan_id,
             COUNT(*) AS task_total,
             SUM(CASE WHEN is_done = 1 THEN 1 ELSE 0 END) AS task_done
         FROM learning_task
         GROUP BY plan_id
     ) AS task_stat ON task_stat.plan_id = lp.id
     LEFT JOIN (
         SELECT plan_id,
             SUM(study_minutes) AS total_minutes
         FROM plan_progress
         GROUP BY plan_id
     ) AS progress_stat ON progress_stat.plan_id = lp.id
        WHERE lp.student_id = %s
        ORDER BY lp.id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.post("/api/student/learning_plan")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_plan_create():
    """学员创建学习计划。"""
    payload = parse_json()
    validate_required(payload, ["title", "start_date", "end_date"])

    title = mask_forbidden_text((payload.get("title") or "").strip())
    target = mask_forbidden_text((payload.get("target") or "").strip()) or None
    start_date = (payload.get("start_date") or "").strip()
    end_date = (payload.get("end_date") or "").strip()
    remind_time = (payload.get("remind_time") or "").strip() or None

    if len(title) > 120:
        raise ValidationError("title 长度不能超过 120")
    if not is_valid_date(start_date) or not is_valid_date(end_date):
        raise ValidationError("start_date/end_date 格式错误，应为 YYYY-MM-DD")
    if start_date > end_date:
        raise ValidationError("start_date 不能晚于 end_date")

    plan_id = insert_and_get_id(
        """
        INSERT INTO learning_plan (student_id, title, target, start_date, end_date, remind_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'ongoing')
        """,
        (int(current_user.id), title, target, start_date, end_date, remind_time),
    )
    return api_resp(200, "创建成功", {"plan_id": plan_id})


@app.put("/api/student/learning_plan/<int:plan_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_plan_update(plan_id):
    """学员编辑自己的学习计划。"""
    payload = parse_json()
    plan = query_one("SELECT id FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能编辑自己的学习计划", {})

    validate_required(payload, ["title", "start_date", "end_date"])
    title = mask_forbidden_text((payload.get("title") or "").strip())
    target = mask_forbidden_text((payload.get("target") or "").strip()) or None
    start_date = (payload.get("start_date") or "").strip()
    end_date = (payload.get("end_date") or "").strip()
    remind_time = (payload.get("remind_time") or "").strip() or None
    if len(title) > 120:
        raise ValidationError("title 长度不能超过 120")
    if not is_valid_date(start_date) or not is_valid_date(end_date):
        raise ValidationError("start_date/end_date 格式错误，应为 YYYY-MM-DD")
    if start_date > end_date:
        raise ValidationError("start_date 不能晚于 end_date")

    execute(
        """
        UPDATE learning_plan
        SET title=%s, target=%s, start_date=%s, end_date=%s, remind_time=%s
        WHERE id=%s
        """,
        (title, target, start_date, end_date, remind_time, plan_id),
    )
    return api_resp(200, "更新成功", {})


@app.delete("/api/student/learning_plan/<int:plan_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_plan_delete(plan_id):
    """学员删除自己的学习计划。"""
    plan = query_one("SELECT id FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能删除自己的学习计划", {})

    execute("DELETE FROM learning_plan WHERE id=%s", (plan_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/student/learning_task_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_task_list():
    """学员查看指定学习计划下的任务列表。"""
    plan_id = normalize_optional_int(request.args.get("plan_id"), "plan_id", min_value=1)
    if plan_id is None:
        raise ValidationError("缺少 plan_id")

    plan = query_one("SELECT id FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能查看自己的学习任务", {})

    rows = query_all(
        """
        SELECT id, plan_id, task_title, task_date, estimated_minutes, sort_no, is_done, done_time, create_time
        FROM learning_task
        WHERE plan_id=%s
        ORDER BY sort_no ASC, id ASC
        """,
        (plan_id,),
    )
    return api_resp(200, "查询成功", rows)


@app.post("/api/student/learning_task")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_task_create():
    """学员创建学习任务。"""
    payload = parse_json()
    validate_required(payload, ["plan_id", "task_title"])

    plan_id = normalize_optional_int(payload.get("plan_id"), "plan_id", min_value=1)
    task_title = mask_forbidden_text((payload.get("task_title") or "").strip())
    task_date = (payload.get("task_date") or "").strip() or None
    estimated_minutes = normalize_optional_int(payload.get("estimated_minutes"), "estimated_minutes", min_value=0, max_value=1440)
    sort_no = normalize_optional_int(payload.get("sort_no"), "sort_no", min_value=0) or 0

    plan = query_one("SELECT id, start_date FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能在自己的学习计划下创建任务", {})
    if len(task_title) > 160:
        raise ValidationError("task_title 长度不能超过 160")
    if task_date and not is_valid_date(task_date):
        raise ValidationError("task_date 格式错误，应为 YYYY-MM-DD")
    if not task_date:
        last_task = query_one(
            "SELECT MAX(task_date) AS last_task_date FROM learning_task WHERE plan_id=%s",
            (plan_id,),
        )
        task_date = build_next_learning_task_date(last_task.get("last_task_date") if last_task else plan.get("start_date"))

    task_id = insert_and_get_id(
        """
        INSERT INTO learning_task (plan_id, task_title, task_date, estimated_minutes, sort_no, is_done)
        VALUES (%s, %s, %s, %s, %s, 0)
        """,
        (plan_id, task_title, task_date, estimated_minutes, sort_no),
    )
    return api_resp(200, "创建成功", {"task_id": task_id})


@app.put("/api/student/learning_task/<int:task_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_task_update(task_id):
    """学员更新学习任务（包含完成状态切换）。"""
    payload = parse_json()
    task = query_one(
        """
        SELECT lt.id, lt.plan_id, lt.task_date AS current_task_date, lp.start_date
        FROM learning_task lt
        JOIN learning_plan lp ON lt.plan_id = lp.id
        WHERE lt.id=%s AND lp.student_id=%s
        """,
        (task_id, int(current_user.id)),
    )
    if not task:
        return api_resp(403, "只能更新自己的学习任务", {})

    validate_required(payload, ["task_title", "is_done"])
    task_title = mask_forbidden_text((payload.get("task_title") or "").strip())
    task_date = (payload.get("task_date") or "").strip() or None
    estimated_minutes = normalize_optional_int(payload.get("estimated_minutes"), "estimated_minutes", min_value=0, max_value=1440)
    sort_no = normalize_optional_int(payload.get("sort_no"), "sort_no", min_value=0) or 0
    is_done = 1 if payload.get("is_done") in [1, True, "1", "true", "True"] else 0

    if len(task_title) > 160:
        raise ValidationError("task_title 长度不能超过 160")
    if task_date and not is_valid_date(task_date):
        raise ValidationError("task_date 格式错误，应为 YYYY-MM-DD")
    if not task_date:
        task_date = task.get("current_task_date")
        if not task_date:
            task_date = build_next_learning_task_date(task.get("start_date"))

    done_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_done else None
    execute(
        """
        UPDATE learning_task
        SET task_title=%s, task_date=%s, estimated_minutes=%s, sort_no=%s, is_done=%s, done_time=%s
        WHERE id=%s
        """,
        (task_title, task_date, estimated_minutes, sort_no, is_done, done_time, task_id),
    )
    return api_resp(200, "更新成功", {})


@app.delete("/api/student/learning_task/<int:task_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_learning_task_delete(task_id):
    """学员删除学习任务。"""
    task = query_one(
        """
        SELECT lt.id
        FROM learning_task lt
        JOIN learning_plan lp ON lt.plan_id = lp.id
        WHERE lt.id=%s AND lp.student_id=%s
        """,
        (task_id, int(current_user.id)),
    )
    if not task:
        return api_resp(403, "只能删除自己的学习任务", {})

    execute("DELETE FROM learning_task WHERE id=%s", (task_id,))
    return api_resp(200, "删除成功", {})


@app.post("/api/student/plan_progress")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_plan_progress_upsert():
    """学员写入学习进度（按计划+日期覆盖）。"""
    payload = parse_json()
    validate_required(payload, ["plan_id", "study_minutes"])

    plan_id = normalize_optional_int(payload.get("plan_id"), "plan_id", min_value=1)
    study_minutes = normalize_optional_int(payload.get("study_minutes"), "study_minutes", min_value=0, max_value=1440)
    progress_date = (payload.get("progress_date") or date.today().strftime("%Y-%m-%d")).strip()
    note = mask_forbidden_text((payload.get("note") or "").strip()) or None

    if not is_valid_date(progress_date):
        raise ValidationError("progress_date 格式错误，应为 YYYY-MM-DD")

    plan = query_one("SELECT id FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能记录自己计划的进度", {})

    exists = query_one("SELECT id FROM plan_progress WHERE plan_id=%s AND progress_date=%s", (plan_id, progress_date))
    if exists:
        execute(
            "UPDATE plan_progress SET study_minutes=%s, note=%s WHERE id=%s",
            (study_minutes, note, exists["id"]),
        )
        return api_resp(200, "进度已更新", {"progress_id": exists["id"]})

    progress_id = insert_and_get_id(
        """
        INSERT INTO plan_progress (plan_id, progress_date, study_minutes, note)
        VALUES (%s, %s, %s, %s)
        """,
        (plan_id, progress_date, study_minutes, note),
    )
    return api_resp(200, "进度记录成功", {"progress_id": progress_id})


@app.get("/api/student/plan_progress_stat")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_plan_progress_stat():
    """学员查看计划进度统计。"""
    plan_id = normalize_optional_int(request.args.get("plan_id"), "plan_id", min_value=1)
    if plan_id is None:
        raise ValidationError("缺少 plan_id")

    plan = query_one("SELECT id FROM learning_plan WHERE id=%s AND student_id=%s", (plan_id, int(current_user.id)))
    if not plan:
        return api_resp(403, "只能查看自己的计划进度", {})

    summary = query_one(
        """
        SELECT COALESCE(SUM(study_minutes), 0) AS total_minutes,
               COUNT(*) AS record_days,
               ROUND(AVG(study_minutes), 2) AS avg_minutes
        FROM plan_progress
        WHERE plan_id=%s
        """,
        (plan_id,),
    )
    list_rows = query_all(
        """
        SELECT id, plan_id, progress_date, study_minutes, note, create_time
        FROM plan_progress
        WHERE plan_id=%s
        ORDER BY progress_date DESC
        """,
        (plan_id,),
    )
    return api_resp(200, "查询成功", {"summary": summary or {}, "list": list_rows})


@app.get("/api/teacher/learning_plan_overview")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_learning_plan_overview():
    """任课老师查看可管理学员学习计划概览。"""
    teacher_id = int(current_user.id)
    teacher_course = resolve_teacher_bound_course(teacher_id)
    is_public_course = teacher_course in ["政治", "英语"]

    if is_public_course:
        students = query_all(
            """
            SELECT s.user_id AS student_id,
                   COALESCE(s.name, u.username) AS student_name,
                   u.username AS student_username
            FROM student_info s
            JOIN users u ON s.user_id = u.id
            ORDER BY student_id DESC
            """
        )
    else:
        students = query_all(
            """
            SELECT s.user_id AS student_id,
                   COALESCE(s.name, u.username) AS student_name,
                   u.username AS student_username
            FROM student_info s
            JOIN users u ON s.user_id = u.id
            WHERE s.teacher_id = %s
            ORDER BY student_id DESC
            """,
            (teacher_id,),
        )

    if not students:
        return api_resp(200, "查询成功", {"teacher_course": teacher_course, "students": []})

    student_ids = [int(item["student_id"]) for item in students if item.get("student_id")]
    placeholders = ", ".join(["%s"] * len(student_ids))

    plan_rows = query_all(
        f"""
        SELECT id, student_id, title, target
        FROM learning_plan
        WHERE student_id IN ({placeholders})
        """,
        tuple(student_ids),
    )

    student_plan_count = {student_id: 0 for student_id in student_ids}
    plan_to_student = {}
    plan_meta = {}
    for row in plan_rows:
        sid = int(row.get("student_id") or 0)
        pid = int(row.get("id") or 0)
        if sid and pid:
            plan_to_student[pid] = sid
            plan_meta[pid] = {
                "title": row.get("title"),
                "target": row.get("target"),
            }

    visible_plan_ids = set()
    if is_public_course:
        visible_plan_ids = set(plan_to_student.keys())
    else:
        for pid, meta in plan_meta.items():
            inferred_plan_course = infer_learning_plan_course(meta.get("title"), meta.get("target"))
            if inferred_plan_course == teacher_course:
                visible_plan_ids.add(pid)

    task_count_map = {student_id: 0 for student_id in student_ids}
    done_task_count_map = {student_id: 0 for student_id in student_ids}
    total_minutes_map = {student_id: 0 for student_id in student_ids}
    if plan_to_student:
        plan_ids = list(plan_to_student.keys())
        plan_placeholders = ", ".join(["%s"] * len(plan_ids))
        task_rows = query_all(
            f"""
            SELECT plan_id, task_title, is_done, estimated_minutes
            FROM learning_task
            WHERE plan_id IN ({plan_placeholders})
            """,
            tuple(plan_ids),
        )

        for task in task_rows:
            if not is_learning_task_visible_for_teacher(task.get("task_title"), teacher_course):
                continue
            plan_id = int(task.get("plan_id") or 0)
            sid = plan_to_student.get(plan_id)
            if not sid:
                continue

            visible_plan_ids.add(plan_id)
            task_count_map[sid] = task_count_map.get(sid, 0) + 1

            if int(task.get("is_done") or 0) == 1:
                done_task_count_map[sid] = done_task_count_map.get(sid, 0) + 1
                # 老师端口径：累计学习时间 = 已完成任务的预计时长合计（分钟）
                total_minutes_map[sid] = total_minutes_map.get(sid, 0) + int(task.get("estimated_minutes") or 0)

    for pid in visible_plan_ids:
        sid = plan_to_student.get(pid)
        if sid:
            student_plan_count[sid] = student_plan_count.get(sid, 0) + 1

    rows = []
    for student in students:
        sid = int(student.get("student_id") or 0)
        rows.append(
            {
                **student,
                "plan_count": int(student_plan_count.get(sid, 0)),
                "task_count": int(task_count_map.get(sid, 0)),
                "done_task_count": int(done_task_count_map.get(sid, 0)),
                "total_minutes": int(total_minutes_map.get(sid, 0)),
            }
        )

    return api_resp(200, "查询成功", {"teacher_course": teacher_course, "students": rows})


@app.post("/api/teacher/learning_plan_template_import")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_learning_plan_template_import():
    """任课老师批量导入学习计划模板到名下学员。"""
    payload = parse_json()
    validate_required(payload, ["student_ids", "title", "start_date", "end_date"])

    student_ids = payload.get("student_ids")
    title = (payload.get("title") or "").strip()
    target = (payload.get("target") or "").strip() or None
    start_date = (payload.get("start_date") or "").strip()
    end_date = (payload.get("end_date") or "").strip()
    tasks = payload.get("tasks") if isinstance(payload.get("tasks"), list) else []

    if not isinstance(student_ids, list) or not student_ids:
        raise ValidationError("student_ids 必须为非空数组")
    if len(title) > 120:
        raise ValidationError("title 长度不能超过 120")
    if not is_valid_date(start_date) or not is_valid_date(end_date):
        raise ValidationError("start_date/end_date 格式错误，应为 YYYY-MM-DD")
    if start_date > end_date:
        raise ValidationError("start_date 不能晚于 end_date")

    cleaned_ids = []
    for item in student_ids:
        try:
            val = int(item)
        except (TypeError, ValueError):
            continue
        if val > 0:
            cleaned_ids.append(val)

    if not cleaned_ids:
        raise ValidationError("student_ids 无有效学员ID")

    teacher_id = int(current_user.id)
    teacher_course = resolve_teacher_bound_course(teacher_id)
    is_public_course = teacher_course in ["政治", "英语"]

    placeholders = ",".join(["%s"] * len(cleaned_ids))
    if is_public_course:
        allowed_rows = query_all(
            f"SELECT user_id FROM student_info WHERE user_id IN ({placeholders})",
            tuple(cleaned_ids),
        )
    else:
        allowed_rows = query_all(
            f"SELECT user_id FROM student_info WHERE teacher_id=%s AND user_id IN ({placeholders})",
            (teacher_id, *cleaned_ids),
        )
    allowed_student_ids = [row["user_id"] for row in allowed_rows]
    if not allowed_student_ids:
        return api_resp(400, "所选学员不在当前老师可管理范围内", {})

    created_plan_ids = []
    for student_id in allowed_student_ids:
        plan_id = insert_and_get_id(
            """
            INSERT INTO learning_plan (student_id, title, target, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, 'ongoing')
            """,
            (student_id, title, target, start_date, end_date),
        )
        created_plan_ids.append(plan_id)
        last_task_date = None

        for index, task in enumerate(tasks):
            if isinstance(task, dict):
                task_title = (task.get("task_title") or "").strip()
                task_date = (task.get("task_date") or "").strip() or None
                estimated_minutes = normalize_optional_int(task.get("estimated_minutes"), "estimated_minutes", min_value=0, max_value=1440)
            else:
                task_title = str(task).strip()
                task_date = None
                estimated_minutes = None

            if not task_title:
                continue
            if len(task_title) > 160:
                task_title = task_title[:160]
            if task_date and not is_valid_date(task_date):
                task_date = None
            if not task_date:
                task_date = build_next_learning_task_date(last_task_date or start_date)
            last_task_date = task_date or last_task_date

            task_title = normalize_task_title_by_teacher_course(task_title, teacher_course)

            insert_and_get_id(
                """
                INSERT INTO learning_task (plan_id, task_title, task_date, estimated_minutes, sort_no, is_done)
                VALUES (%s, %s, %s, %s, %s, 0)
                """,
                (plan_id, task_title, task_date, estimated_minutes, index),
            )

    return api_resp(200, "模板导入成功", {"plan_count": len(created_plan_ids), "student_count": len(allowed_student_ids)})


@app.post("/api/teacher/learning_task")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_learning_task_create():
    """任课老师在可管理学员的学习计划下创建任务。"""
    payload = parse_json()
    validate_required(payload, ["plan_id", "task_title"])

    teacher_id = int(current_user.id)
    teacher_course = resolve_teacher_bound_course(teacher_id)
    is_public_course = teacher_course in ["政治", "英语"]

    plan_id = normalize_optional_int(payload.get("plan_id"), "plan_id", min_value=1)
    task_title = (payload.get("task_title") or "").strip()
    task_date = (payload.get("task_date") or "").strip() or None
    estimated_minutes = normalize_optional_int(payload.get("estimated_minutes"), "estimated_minutes", min_value=0, max_value=1440)
    sort_no = normalize_optional_int(payload.get("sort_no"), "sort_no", min_value=0)

    if len(task_title) > 160:
        raise ValidationError("task_title 长度不能超过 160")
    if task_date and not is_valid_date(task_date):
        raise ValidationError("task_date 格式错误，应为 YYYY-MM-DD")

    task_title = normalize_task_title_by_teacher_course(task_title, teacher_course)

    if is_public_course:
        plan = query_one(
            """
            SELECT lp.id, lp.student_id
            FROM learning_plan lp
            JOIN student_info s ON s.user_id = lp.student_id
            WHERE lp.id=%s
            LIMIT 1
            """,
            (plan_id,),
        )
    else:
        plan = query_one(
            """
            SELECT lp.id, lp.student_id
            FROM learning_plan lp
            JOIN student_info s ON s.user_id = lp.student_id
            WHERE lp.id=%s AND s.teacher_id=%s
            LIMIT 1
            """,
            (plan_id, teacher_id),
        )

    if not plan:
        return api_resp(403, "只能给可管理学员的学习计划创建任务", {})

    if sort_no is None:
        last_sort = query_one("SELECT COALESCE(MAX(sort_no), -1) AS max_sort FROM learning_task WHERE plan_id=%s", (plan_id,))
        sort_no = int(last_sort.get("max_sort") or -1) + 1

    task_id = insert_and_get_id(
        """
        INSERT INTO learning_task (plan_id, task_title, task_date, estimated_minutes, sort_no, is_done)
        VALUES (%s, %s, %s, %s, %s, 0)
        """,
        (plan_id, task_title, task_date, estimated_minutes, sort_no),
    )

    create_notification(
        "user",
        title="学习任务已更新",
        content=f"老师 {current_user.username} 在你的学习计划中新增了任务：{task_title}",
        category="learning_plan",
        level="info",
        target_user_id=int(plan["student_id"]),
        action_path="/app/student/learning-plan",
    )

    return api_resp(200, "创建成功", {"task_id": task_id})


@app.get("/api/teacher/student_learning_plan_detail")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_student_learning_plan_detail():
    """任课老师查看指定学员学习计划详情。"""
    student_id = normalize_optional_int(request.args.get("student_id"), "student_id", min_value=1)
    if student_id is None:
        raise ValidationError("缺少 student_id")

    teacher_id = int(current_user.id)
    bound_course = resolve_teacher_bound_course(teacher_id)
    is_public_course = bound_course in ["政治", "英语"]

    if is_public_course:
        student = query_one(
            """
            SELECT s.user_id AS student_id,
                   COALESCE(s.name, u.username) AS student_name,
                   u.username AS student_username
            FROM student_info s
            JOIN users u ON u.id = s.user_id
            WHERE s.user_id=%s
            LIMIT 1
            """,
            (student_id,),
        )
    else:
        student = query_one(
            """
            SELECT s.user_id AS student_id,
                   COALESCE(s.name, u.username) AS student_name,
                   u.username AS student_username
            FROM student_info s
            JOIN users u ON u.id = s.user_id
            WHERE s.user_id=%s AND s.teacher_id=%s
            LIMIT 1
            """,
            (student_id, teacher_id),
        )

    if not student:
        return api_resp(403, "该学员不在当前老师可查看范围内", {})

    plans = query_all(
        """
        SELECT lp.id, lp.title, lp.target, lp.start_date, lp.end_date,
               COALESCE(task_stat.task_total, 0) AS task_total,
               COALESCE(task_stat.task_done, 0) AS task_done,
               COALESCE(progress_stat.total_minutes, 0) AS total_minutes
        FROM learning_plan lp
        LEFT JOIN (
            SELECT plan_id,
                   COUNT(*) AS task_total,
                   SUM(CASE WHEN is_done = 1 THEN 1 ELSE 0 END) AS task_done
            FROM learning_task
            GROUP BY plan_id
        ) AS task_stat ON task_stat.plan_id = lp.id
        LEFT JOIN (
            SELECT plan_id,
                   SUM(study_minutes) AS total_minutes
            FROM plan_progress
            GROUP BY plan_id
        ) AS progress_stat ON progress_stat.plan_id = lp.id
        WHERE lp.student_id=%s
        ORDER BY lp.id DESC
        """,
        (student_id,),
    )

    tasks = query_all(
        """
        SELECT lt.id, lt.plan_id, lp.title AS plan_title, lt.task_title, lt.task_date,
               lt.estimated_minutes, lt.is_done, lt.done_time
        FROM learning_task lt
        JOIN learning_plan lp ON lp.id = lt.plan_id
        WHERE lp.student_id=%s
        ORDER BY COALESCE(lt.task_date, '9999-12-31') ASC, lt.sort_no ASC, lt.id ASC
        LIMIT 200
        """,
        (student_id,),
    )

    teacher_course = resolve_teacher_bound_course(teacher_id)
    tasks = [item for item in tasks if is_learning_task_visible_for_teacher(item.get("task_title"), teacher_course)]

    task_stat_map = {}
    plan_done_minutes_map = {}
    for item in tasks:
        plan_key = int(item.get("plan_id") or 0)
        if plan_key not in task_stat_map:
            task_stat_map[plan_key] = {"task_total": 0, "task_done": 0}
        if plan_key not in plan_done_minutes_map:
            plan_done_minutes_map[plan_key] = 0
        task_stat_map[plan_key]["task_total"] += 1
        if int(item.get("is_done") or 0) == 1:
            task_stat_map[plan_key]["task_done"] += 1
            plan_done_minutes_map[plan_key] = plan_done_minutes_map.get(plan_key, 0) + int(item.get("estimated_minutes") or 0)

    for plan in plans:
        key = int(plan.get("id") or 0)
        stat = task_stat_map.get(key, {"task_total": 0, "task_done": 0})
        plan["task_total"] = stat["task_total"]
        plan["task_done"] = stat["task_done"]
        # 老师端口径：累计学习时间 = 已完成任务预计时长合计（分钟）
        plan["total_minutes"] = int(plan_done_minutes_map.get(key, 0))

    progress = query_all(
        """
        SELECT pp.id, pp.plan_id, lp.title AS plan_title, pp.progress_date, pp.study_minutes, pp.note
        FROM plan_progress pp
        JOIN learning_plan lp ON lp.id = pp.plan_id
        WHERE lp.student_id=%s
        ORDER BY pp.progress_date DESC, pp.id DESC
        LIMIT 60
        """,
        (student_id,),
    )

    if bound_course and bound_course not in ["政治", "英语"]:
        filtered_plans = []
        for plan in plans:
            inferred_plan_course = infer_learning_plan_course(plan.get("title"), plan.get("target"))
            has_visible_tasks = int(plan.get("task_total") or 0) > 0
            if inferred_plan_course:
                # 计划标题/目标可能同时包含“政治、英语、专业课”，
                # 若该计划下存在当前课程可见任务，也应保留。
                if inferred_plan_course == bound_course or has_visible_tasks:
                    filtered_plans.append(plan)
                continue
            if has_visible_tasks:
                filtered_plans.append(plan)
        plans = filtered_plans

        visible_plan_ids = {int(item.get("id") or 0) for item in plans}
        tasks = [item for item in tasks if int(item.get("plan_id") or 0) in visible_plan_ids]
        progress = [item for item in progress if int(item.get("plan_id") or 0) in visible_plan_ids]

        filtered_progress = []
        for item in progress:
            note_course = infer_learning_task_course(item.get("note"))
            # 备注未命中课程关键词时视为通用内容，保留展示；
            # 若明确命中他课关键词（如英语/政治），则对专业课老师隐藏。
            if note_course and note_course != bound_course:
                continue
            filtered_progress.append(item)
        progress = filtered_progress

    summary = {
        "plan_count": len(plans),
        "task_total": int(sum(int(item.get("task_total") or 0) for item in plans)),
        "task_done": int(sum(int(item.get("task_done") or 0) for item in plans)),
        "total_minutes": int(sum(int(item.get("total_minutes") or 0) for item in plans)),
    }
    summary["completion_rate"] = round((summary["task_done"] / summary["task_total"] * 100), 1) if summary["task_total"] else 0

    return api_resp(
        200,
        "查询成功",
        {
            "student": student,
            "summary": summary,
            "plans": plans,
            "tasks": tasks,
            "progress": progress,
        },
    )


# ==============================
# 考试模拟接口
# ==============================
def normalize_answer_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_multi_answer(value):
    if value is None:
        return ""
    text = str(value).strip().upper().replace("，", ";").replace(",", ";")
    parts = [p.strip() for p in text.split(";") if p.strip()]
    normalized = []
    for part in parts:
        letter_match = re.match(r"^([A-Z])", part)
        normalized.append(letter_match.group(1) if letter_match else part)
    normalized = sorted(set(normalized))
    return ";".join(normalized)


ALL_QUESTION_TYPES = ["single", "multi", "pair", "judge", "fill", "term", "short", "essay"]
OBJECTIVE_QUESTION_TYPES = ["single", "multi", "pair", "judge", "fill"]
SUBJECTIVE_QUESTION_TYPES = ["term", "short", "essay"]


def get_question_bank_non_template_where(alias=""):
    prefix = f"{alias}." if alias else ""
    return " AND ".join(
        [
            f"({prefix}source IS NULL OR {prefix}source NOT LIKE '%%高质量原创模拟题%%')",
            f"{prefix}content NOT LIKE '%%系统补齐%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》单选题%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》多选题%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》配伍题%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》填空题%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》名词解释%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》简答题%%'",
            f"{prefix}content NOT LIKE '%%第%%节《%%》论述题%%'",
        ]
    )


def ensure_question_bank_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS question_bank (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '题库题目ID',
            course VARCHAR(100) NOT NULL COMMENT '课程名称',
            section_no INT NOT NULL COMMENT '章节序号',
            section_title VARCHAR(120) NOT NULL COMMENT '章节标题',
            question_type ENUM('single','multi','pair','judge','fill','term','short','essay') NOT NULL COMMENT '题型',
            difficulty ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium' COMMENT '难度',
            knowledge_point VARCHAR(120) DEFAULT NULL COMMENT '知识点',
            content TEXT NOT NULL COMMENT '题干',
            options_json TEXT COMMENT '选择题选项JSON',
            correct_answer TEXT COMMENT '标准答案',
            analysis TEXT COMMENT '解析',
            score DECIMAL(6,2) NOT NULL DEFAULT 0 COMMENT '默认分值',
            source VARCHAR(120) DEFAULT NULL COMMENT '题目来源',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_question_bank_course_section (course, section_no),
            INDEX idx_question_bank_type (question_type),
            INDEX idx_question_bank_difficulty (difficulty),
            INDEX idx_question_bank_knowledge_point (knowledge_point)
        ) ENGINE=InnoDB COMMENT='考试题库表'
        """
    )


def ensure_question_bank_enhanced_schema():
    execute(
        """
        ALTER TABLE question_bank
        MODIFY COLUMN question_type ENUM('single','multi','pair','judge','fill','term','short','essay') NOT NULL COMMENT '题型'
        """
    )

    column_specs = [
        ("difficulty", "ALTER TABLE question_bank ADD COLUMN difficulty ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium' COMMENT '难度'"),
        ("knowledge_point", "ALTER TABLE question_bank ADD COLUMN knowledge_point VARCHAR(120) DEFAULT NULL COMMENT '知识点'"),
        ("source", "ALTER TABLE question_bank ADD COLUMN source VARCHAR(120) DEFAULT NULL COMMENT '题目来源'"),
    ]
    for column_name, ddl in column_specs:
        exists = query_one(
            """
            SELECT COUNT(*) AS total
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'question_bank'
              AND COLUMN_NAME = %s
            """,
            (column_name,),
        )
        if int((exists or {}).get("total") or 0) > 0:
            continue
        execute(ddl)


def ensure_question_bank_stats_view():
    execute("DROP VIEW IF EXISTS question_bank_stats")
    execute(
        """
        CREATE VIEW question_bank_stats AS
        SELECT
            course,
            section_no AS chapter_no,
            section_title AS chapter_title,
            question_type,
            difficulty,
            COUNT(*) AS question_count
        FROM question_bank
        GROUP BY course, section_no, section_title, question_type, difficulty
        """
    )


def ensure_teacher_course_binding_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_course_binding (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '绑定ID',
            teacher_id INT NOT NULL COMMENT '老师ID（users.id）',
            course VARCHAR(100) NOT NULL COMMENT '绑定课程',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            UNIQUE KEY uk_teacher_course_binding_teacher (teacher_id),
            INDEX idx_teacher_course_binding_course (course),
            CONSTRAINT fk_teacher_course_binding_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='老师课程绑定表'
        """
    )


def ensure_teacher_profile_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_profile (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '档案ID',
            teacher_id INT NOT NULL COMMENT '老师ID（users.id）',
            name VARCHAR(50) NOT NULL COMMENT '姓名',
            gender ENUM('男','女') NOT NULL DEFAULT '男' COMMENT '性别',
            phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
            email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
            bio VARCHAR(500) DEFAULT NULL COMMENT '个人简介',
            create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            UNIQUE KEY uk_teacher_profile_teacher (teacher_id),
            INDEX idx_teacher_profile_name (name),
            CONSTRAINT fk_teacher_profile_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB COMMENT='老师个人档案表'
        """
    )


def ensure_teacher_profile_columns():
    """兼容历史 teacher_profile 结构，确保 bio/intro 字段都存在。"""
    extra_columns = [
        (
            "bio",
            "ALTER TABLE teacher_profile ADD COLUMN bio VARCHAR(500) DEFAULT NULL COMMENT '个人简介' AFTER email",
        ),
        (
            "intro",
            "ALTER TABLE teacher_profile ADD COLUMN intro VARCHAR(500) DEFAULT NULL COMMENT '个人简介（兼容旧字段）' AFTER bio",
        ),
    ]
    for column_name, ddl in extra_columns:
        exists = query_one(
            """
            SELECT COUNT(1) AS total
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'teacher_profile'
              AND COLUMN_NAME = %s
            """,
            (column_name,),
        )
        if int((exists or {}).get("total") or 0) > 0:
            continue
        execute(ddl)


def seed_default_teacher_profiles():
    default_profiles = {
        "李明": {
            "name": "李明",
            "gender": "男",
            "phone": "13800000001",
            "email": "liming@hongshi.edu.cn",
            "bio": "临床医学方向授课教师，长期负责医学综合课程与题型训练。",
        },
        "周凯": {
            "name": "周凯",
            "gender": "男",
            "phone": "13800000002",
            "email": "zhoukai@hongshi.edu.cn",
            "bio": "中医临床方向授课教师，注重辨证思维与高频考点梳理。",
        },
        "陈洁": {
            "name": "陈洁",
            "gender": "女",
            "phone": "13800000003",
            "email": "chenjie@hongshi.edu.cn",
            "bio": "口腔医学方向授课教师，擅长专项能力提升与案例讲解。",
        },
        "刘颖": {
            "name": "刘颖",
            "gender": "女",
            "phone": "13800000004",
            "email": "liuying@hongshi.edu.cn",
            "bio": "护理与医学技术综合方向授课教师，负责跨学科知识体系搭建。",
        },
        "王雪": {
            "name": "王雪",
            "gender": "女",
            "phone": "13800000005",
            "email": "wangxue@hongshi.edu.cn",
            "bio": "政治课程授课教师，专注时政热点与主观题答题逻辑训练。",
        },
        "赵宁": {
            "name": "赵宁",
            "gender": "男",
            "phone": "13800000006",
            "email": "zhaoning@hongshi.edu.cn",
            "bio": "英语课程授课教师，聚焦词汇语法体系与阅读写作能力提升。",
        },
    }

    rows = query_all("SELECT id, username FROM users WHERE role='teacher'")
    for row in rows:
        username = (row.get("username") or "").strip()
        if not username:
            continue
        profile = default_profiles.get(username, {})
        execute(
            """
            INSERT INTO teacher_profile (teacher_id, name, gender, phone, email, bio, intro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                gender=VALUES(gender),
                phone=COALESCE(teacher_profile.phone, VALUES(phone)),
                email=COALESCE(teacher_profile.email, VALUES(email)),
                bio=COALESCE(teacher_profile.bio, VALUES(bio)),
                intro=COALESCE(teacher_profile.intro, VALUES(intro))
            """,
            (
                int(row["id"]),
                profile.get("name") or username,
                profile.get("gender") or "男",
                profile.get("phone"),
                profile.get("email"),
                profile.get("bio"),
                profile.get("bio"),
            ),
        )


def seed_default_teacher_course_bindings():
    default_bindings = {
        "李明": "西医临床",
        "周凯": "中医临床",
        "陈洁": "口腔医学",
        "刘颖": "其他类（护理学、医学技术、基础医学、公共卫生等）",
        "王雪": "政治",
        "赵宁": "英语",
    }

    for username, course in default_bindings.items():
        teacher = query_one(
            "SELECT id FROM users WHERE username=%s AND role='teacher' LIMIT 1",
            (username,),
        )
        if not teacher:
            continue
        execute(
            """
            INSERT INTO teacher_course_binding (teacher_id, course)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE course=VALUES(course)
            """,
            (int(teacher["id"]), course),
        )


def extract_course_from_exam_title(title):
    if not title:
        return None
    clean_title = str(title).strip()
    if not clean_title:
        return None

    patterns = [
        r"^(.+?)课程(?:测验|考试)",
        r"^(.+?)第\d+节测验",
    ]
    for pattern in patterns:
        matched = re.match(pattern, clean_title)
        if matched:
            return matched.group(1).strip()
    return None


def infer_teacher_course(teacher_id):
    rows = query_all(
        "SELECT title FROM exam WHERE teacher_id=%s ORDER BY id DESC LIMIT 5",
        (int(teacher_id),),
    )
    for row in rows:
        course = extract_course_from_exam_title(row.get("title"))
        if course:
            return course

    row = query_one(
        "SELECT title FROM homework WHERE teacher_id=%s ORDER BY id DESC LIMIT 1",
        (int(teacher_id),),
    )
    if row and row.get("title"):
        title = str(row["title"])
        marker = "课程"
        if marker in title:
            return title.split(marker)[0].strip() or None

    return None


def resolve_teacher_bound_course(teacher_id):
    binding = query_one(
        "SELECT course FROM teacher_course_binding WHERE teacher_id=%s LIMIT 1",
        (int(teacher_id),),
    )
    if binding and binding.get("course"):
        return str(binding["course"])

    inferred_course = infer_teacher_course(teacher_id)
    if inferred_course:
        execute(
            """
            INSERT INTO teacher_course_binding (teacher_id, course)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE course=VALUES(course)
            """,
            (int(teacher_id), inferred_course),
        )
        return inferred_course
    return None


def get_course_type_preference(course):
    blueprint = get_course_exam_blueprint().get(course)
    if blueprint and blueprint.get("type_ratio"):
        ratio = blueprint["type_ratio"]
        return {k: int(float(ratio.get(k, 0.0)) * 100) for k in ALL_QUESTION_TYPES}
    return {"single": 60, "multi": 20, "pair": 10, "judge": 0, "fill": 5, "term": 0, "short": 5, "essay": 0}


def get_course_exam_blueprint():
    return {
        "西医临床": {
            "chapter_min": 10,
            "type_ratio": {"single": 0.55, "pair": 0.20, "multi": 0.25},
            "chapters": {
                1: "内科学（心血管、呼吸、消化、内分泌、肾脏、血液系统）",
                2: "外科学（普外、骨科、泌尿、胸外、神外）",
                3: "妇产科学",
                4: "儿科学",
                5: "诊断学",
                6: "病理学",
                7: "药理学",
                8: "基础医学（生理学、生物化学、解剖学）",
            },
        },
        "中医临床": {
            "chapter_min": 8,
            "type_ratio": {"single": 0.55, "pair": 0.20, "multi": 0.25},
            "chapters": {
                1: "中医基础理论（阴阳五行、脏腑经络、气血津液）",
                2: "中医诊断学（四诊、辨证方法）",
                3: "中药学（常用中药性能、配伍禁忌）",
                4: "方剂学（常用方剂组成、功效、主治）",
                5: "中医内科学（常见病证辨证论治）",
                6: "针灸学（经络腧穴、针灸治疗）",
            },
        },
        "口腔医学": {
            "chapter_min": 8,
            "type_ratio": {"single": 0.45, "multi": 0.20, "term": 0.15, "short": 0.10, "essay": 0.10},
            "chapters": {
                1: "口腔解剖生理学",
                2: "口腔组织病理学",
                3: "牙体牙髓病学",
                4: "牙周病学",
                5: "口腔颌面外科学",
            },
        },
        "其他类（护理学、医学技术、基础医学、公共卫生等）": {
            "chapter_min": 8,
            "type_ratio": {"single": 0.40, "multi": 0.20, "term": 0.15, "short": 0.15, "essay": 0.10},
            "chapters": {
                1: "护理学基础（护理程序、基础护理技术）",
                2: "内科护理学",
                3: "外科护理学",
                4: "医学统计学",
                5: "流行病学",
                6: "公共卫生学",
            },
        },
        "政治": {
            "chapter_min": 10,
            "type_ratio": {"single": 0.45, "multi": 0.35, "short": 0.20},
            "chapters": {
                1: "马克思主义基本原理（唯物论、辩证法、认识论、唯物史观）",
                2: "毛泽东思想和中国特色社会主义理论体系概论",
                3: "中国近现代史纲要",
                4: "思想道德修养与法律基础",
                5: "形势与政策（时事政治）",
            },
        },
        "英语": {
            "chapter_min": 8,
            "type_ratio": {"single": 0.70, "fill": 0.15, "short": 0.15},
            "chapters": {
                1: "阅读理解技巧（主旨题、细节题、推理题）",
                2: "完形填空技巧（词汇辨析、语法结构、逻辑关系）",
                3: "翻译技巧（长难句分析、翻译方法）",
                4: "写作技巧（应用文、图画作文、议论文）",
                5: "词汇与语法（高频词汇、语法要点）",
            },
        },
    }


def get_allowed_question_types(course):
    blueprint = get_course_exam_blueprint().get(course)
    if not blueprint:
        return ALL_QUESTION_TYPES
    ratio = blueprint.get("type_ratio") or {}
    allowed = [k for k in ALL_QUESTION_TYPES if float(ratio.get(k, 0.0)) > 0]
    return allowed or ALL_QUESTION_TYPES


def rebalance_counts_by_course(course, type_counts):
    total = sum(int(type_counts.get(k) or 0) for k in ALL_QUESTION_TYPES)
    if total <= 0:
        return type_counts

    pref = get_course_type_preference(course)
    weight_sum = sum(pref.values()) or 1
    rebalanced = {k: 0 for k in ALL_QUESTION_TYPES}
    fractions = []

    for key in ALL_QUESTION_TYPES:
        raw = total * (float(pref.get(key, 0)) / weight_sum)
        base = int(math.floor(raw))
        rebalanced[key] = base
        fractions.append((raw - base, key))

    remains = total - sum(rebalanced.values())
    fractions.sort(reverse=True)
    idx = 0
    while remains > 0 and idx < len(fractions):
        key = fractions[idx][1]
        rebalanced[key] += 1
        remains -= 1
        idx += 1

    for key in ALL_QUESTION_TYPES:
        if float(pref.get(key, 0)) == 0 and rebalanced.get(key, 0) > 0:
            rebalanced["single"] += rebalanced[key]
            rebalanced[key] = 0

    if rebalanced.get("single", 0) <= 0 and total > 0:
        for donor in ["multi", "pair", "fill", "short", "term", "essay", "judge"]:
            if rebalanced.get(donor, 0) > 0:
                rebalanced[donor] -= 1
                rebalanced["single"] = 1
                break

    return rebalanced


try:
    ensure_question_bank_table()
except Exception:
    app.logger.exception("初始化题库表失败，可能是数据库连接异常")

try:
    ensure_question_bank_enhanced_schema()
except Exception:
    app.logger.exception("增强题库字段失败，可能是数据库连接异常")

try:
    ensure_question_bank_stats_view()
except Exception:
    app.logger.exception("初始化题库统计视图失败，可能是数据库连接异常")

try:
    ensure_teacher_course_binding_table()
except Exception:
    app.logger.exception("初始化老师课程绑定表失败，可能是数据库连接异常")

try:
    ensure_teacher_profile_table()
except Exception:
    app.logger.exception("初始化老师档案表失败，可能是数据库连接异常")

try:
    ensure_teacher_profile_columns()
except Exception:
    app.logger.exception("迁移老师档案字段失败，可能是数据库连接异常")

try:
    seed_default_teacher_course_bindings()
except Exception:
    app.logger.exception("初始化默认老师课程绑定失败，可能是数据库连接异常")

try:
    seed_default_teacher_profiles()
except Exception:
    app.logger.exception("初始化默认老师档案失败，可能是数据库连接异常")


@app.post("/api/teacher/exam")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_create():
    """任课老师创建考试并批量添加题目。"""
    payload = parse_json()
    validate_required(payload, ["title", "start_time", "end_time", "duration_minutes", "questions"])

    title = mask_forbidden_text((payload.get("title") or "").strip())
    description = mask_forbidden_text((payload.get("description") or "").strip()) or None
    start_time = (payload.get("start_time") or "").strip()
    end_time = (payload.get("end_time") or "").strip()
    duration_minutes = normalize_optional_int(payload.get("duration_minutes"), "duration_minutes", min_value=10, max_value=600)
    status = (payload.get("status") or "published").strip()
    questions = payload.get("questions")

    if len(title) > 160:
        raise ValidationError("title 长度不能超过 160")
    if status not in ["draft", "published", "closed"]:
        raise ValidationError("status 非法，仅支持 draft/published/closed")
    if not is_valid_datetime(start_time) or not is_valid_datetime(end_time):
        raise ValidationError("start_time/end_time 格式错误，应为 YYYY-MM-DD HH:MM:SS")
    if start_time >= end_time:
        raise ValidationError("start_time 必须早于 end_time")
    if not isinstance(questions, list) or not questions:
        raise ValidationError("questions 必须为非空数组")

    teacher_course = resolve_teacher_bound_course(int(current_user.id))
    if not teacher_course:
        return api_resp(400, "当前老师尚未绑定教学课程，请联系管理员", {})
    allowed_types = set(get_allowed_question_types(teacher_course))

    supported_types = ALL_QUESTION_TYPES
    fixed_score_map = {
        "single": 5,
        "multi": 2,
        "pair": 2,
        "judge": 4,
        "fill": 6,
        "term": 8,
        "short": 10,
        "essay": 12,
    }
    normalized_questions = []
    for index, item in enumerate(questions):
        if not isinstance(item, dict):
            continue
        question_type = (item.get("question_type") or "").strip()
        content = mask_forbidden_text((item.get("content") or "").strip())
        options = item.get("options") if isinstance(item.get("options"), list) else []
        correct_answer = mask_forbidden_text((item.get("correct_answer") or "").strip()) or None
        analysis = mask_forbidden_text((item.get("analysis") or "").strip()) or None

        if question_type not in supported_types:
            raise ValidationError("question_type 非法，仅支持 single/multi/pair/judge/fill/term/short/essay")
        if question_type not in allowed_types:
            raise ValidationError(f"当前课程【{teacher_course}】不支持题型 {question_type}")
        if not content:
            raise ValidationError("题目 content 不能为空")
        if question_type in ["single", "multi", "pair"] and not options:
            raise ValidationError("single/multi/pair 题型必须提供 options")
        if question_type == "judge" and correct_answer not in ["正确", "错误"]:
            raise ValidationError("judge 题型标准答案只能为 正确 或 错误")
        score = fixed_score_map[question_type]

        options_json = json.dumps(options, ensure_ascii=False) if options else None
        normalized_questions.append(
            {
                "question_type": question_type,
                "content": content,
                "options_json": options_json,
                "correct_answer": correct_answer,
                "analysis": analysis,
                "score": score,
                "sort_no": index,
            }
        )

    if not normalized_questions:
        raise ValidationError("questions 中没有可用题目")

    exam_id = insert_and_get_id(
        """
        INSERT INTO exam (teacher_id, title, description, start_time, end_time, duration_minutes, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (int(current_user.id), title, description, start_time, end_time, duration_minutes, status),
    )

    for item in normalized_questions:
        insert_and_get_id(
            """
            INSERT INTO question (exam_id, question_type, content, options_json, correct_answer, analysis, score, sort_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                exam_id,
                item["question_type"],
                item["content"],
                item["options_json"],
                item["correct_answer"],
                item["analysis"],
                item["score"],
                item["sort_no"],
            ),
        )

    student_rows = query_all(
        "SELECT user_id FROM student_info WHERE teacher_id=%s",
        (int(current_user.id),),
    )
    for row in student_rows:
        create_notification(
            "user",
            title=f"新模拟考试：{title}",
            content=f"老师 {current_user.username} 发布了新的模拟考试，请按时完成作答。",
            category="exam",
            level="info",
            target_user_id=int(row["user_id"]),
            action_path="/app/student/exam-center",
        )

    create_notification(
        "admin",
        title="新增模拟考试",
        content=f"教师 {current_user.username} 发布了考试《{title}》。",
        category="exam",
        level="warning",
        action_path="/admin/notifications",
    )

    return api_resp(200, "考试创建成功", {"exam_id": exam_id, "question_count": len(normalized_questions)})


@app.get("/api/teacher/exam_question_bank_meta")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_question_bank_meta():
    teacher_id = int(current_user.id)
    bound_course = resolve_teacher_bound_course(teacher_id)
    if not bound_course:
        return api_resp(400, "当前老师尚未绑定教学课程，请联系管理员", {})

    rows = query_all(
                f"""
        SELECT course, section_no, section_title,
               SUM(CASE WHEN question_type='single' THEN 1 ELSE 0 END) AS single_count,
             SUM(CASE WHEN question_type='multi' THEN 1 ELSE 0 END) AS multi_count,
             SUM(CASE WHEN question_type='pair' THEN 1 ELSE 0 END) AS pair_count,
               SUM(CASE WHEN question_type='judge' THEN 1 ELSE 0 END) AS judge_count,
               SUM(CASE WHEN question_type='fill' THEN 1 ELSE 0 END) AS fill_count,
             SUM(CASE WHEN question_type='term' THEN 1 ELSE 0 END) AS term_count,
             SUM(CASE WHEN question_type='short' THEN 1 ELSE 0 END) AS short_count,
             SUM(CASE WHEN question_type='essay' THEN 1 ELSE 0 END) AS essay_count
        FROM question_bank
                WHERE course=%s AND {get_question_bank_non_template_where()}
        GROUP BY course, section_no, section_title
        ORDER BY course ASC, section_no ASC
        """,
        (bound_course,),
    )

    grouped = {}
    for row in rows:
        course = row["course"]
        if course not in grouped:
            grouped[course] = {"course": course, "sections": []}
        grouped[course]["sections"].append(
            {
                "section_no": row["section_no"],
                "section_title": row["section_title"],
                "counts": {
                    "single": int(row.get("single_count") or 0),
                    "multi": int(row.get("multi_count") or 0),
                    "pair": int(row.get("pair_count") or 0),
                    "judge": int(row.get("judge_count") or 0),
                    "fill": int(row.get("fill_count") or 0),
                    "term": int(row.get("term_count") or 0),
                    "short": int(row.get("short_count") or 0),
                    "essay": int(row.get("essay_count") or 0),
                },
            }
        )

    return api_resp(200, "查询成功", list(grouped.values()))


@app.get("/api/teacher/question_bank_stats")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_question_bank_stats():
    teacher_id = int(current_user.id)
    bound_course = resolve_teacher_bound_course(teacher_id)
    if not bound_course:
        return api_resp(400, "当前老师尚未绑定教学课程，请联系管理员", {})

    section_no = normalize_optional_int(request.args.get("section_no"), "section_no", min_value=1)
    question_type = (request.args.get("question_type") or "").strip()
    difficulty = (request.args.get("difficulty") or "").strip()

    where_sql = ["course=%s"]
    params = [bound_course]
    if section_no:
        where_sql.append("chapter_no=%s")
        params.append(section_no)
    if question_type in ALL_QUESTION_TYPES:
        where_sql.append("question_type=%s")
        params.append(question_type)
    if difficulty in ["easy", "medium", "hard"]:
        where_sql.append("difficulty=%s")
        params.append(difficulty)

    rows = query_all(
        f"""
        SELECT course, chapter_no AS section_no, chapter_title AS section_title,
               question_type, difficulty, question_count
        FROM question_bank_stats
        WHERE {' AND '.join(where_sql)}
        ORDER BY chapter_no ASC, question_type ASC, difficulty ASC
        """,
        tuple(params),
    )

    summary = query_one(
        f"""
        SELECT
            COALESCE(SUM(question_count), 0) AS total,
            COALESCE(SUM(CASE WHEN question_type='single' THEN question_count ELSE 0 END), 0) AS single_total,
            COALESCE(SUM(CASE WHEN question_type='multi' THEN question_count ELSE 0 END), 0) AS multi_total,
            COALESCE(SUM(CASE WHEN question_type='pair' THEN question_count ELSE 0 END), 0) AS pair_total,
            COALESCE(SUM(CASE WHEN question_type='judge' THEN question_count ELSE 0 END), 0) AS judge_total,
            COALESCE(SUM(CASE WHEN question_type='fill' THEN question_count ELSE 0 END), 0) AS fill_total,
            COALESCE(SUM(CASE WHEN question_type='term' THEN question_count ELSE 0 END), 0) AS term_total,
            COALESCE(SUM(CASE WHEN question_type='short' THEN question_count ELSE 0 END), 0) AS short_total,
            COALESCE(SUM(CASE WHEN question_type='essay' THEN question_count ELSE 0 END), 0) AS essay_total
        FROM question_bank_stats
        WHERE {' AND '.join(where_sql)}
        """,
        tuple(params),
    )

    return api_resp(200, "查询成功", {"rows": rows, "summary": summary or {}})


@app.post("/api/teacher/exam_question_bank_generate")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_question_bank_generate():
    payload = parse_json()
    validate_required(payload, ["course", "section_no", "counts"])

    course = mask_forbidden_text((payload.get("course") or "").strip())
    section_no = normalize_optional_int(payload.get("section_no"), "section_no", min_value=1)
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}

    type_counts = {
        "single": normalize_optional_int(counts.get("single", 0), "single", min_value=0) or 0,
        "multi": normalize_optional_int(counts.get("multi", 0), "multi", min_value=0) or 0,
        "pair": normalize_optional_int(counts.get("pair", 0), "pair", min_value=0) or 0,
        "judge": normalize_optional_int(counts.get("judge", 0), "judge", min_value=0) or 0,
        "fill": normalize_optional_int(counts.get("fill", 0), "fill", min_value=0) or 0,
        "term": normalize_optional_int(counts.get("term", 0), "term", min_value=0) or 0,
        "short": normalize_optional_int(counts.get("short", 0), "short", min_value=0) or 0,
        "essay": normalize_optional_int(counts.get("essay", 0), "essay", min_value=0) or 0,
    }
    auto_mix = bool(payload.get("auto_mix", True))
    if auto_mix:
        type_counts = rebalance_counts_by_course(course, type_counts)

    total_count = sum(type_counts.values())
    if total_count <= 0:
        raise ValidationError("请至少选择一种题型数量")

    teacher_id = int(current_user.id)
    bound_course = resolve_teacher_bound_course(teacher_id)
    if not bound_course:
        return api_resp(400, "当前老师尚未绑定教学课程，请联系管理员", {})
    if course != bound_course:
        return api_resp(400, f"当前老师仅允许创建课程【{bound_course}】的考试", {})

    allowed_types = set(get_allowed_question_types(course))
    type_label_map = {
        "single": "单选题",
        "multi": "多选题",
        "pair": "配伍题",
        "judge": "判断题",
        "fill": "填空题",
        "term": "名词解释",
        "short": "简答题",
        "essay": "论述题",
    }

    for key, value in type_counts.items():
        if int(value or 0) > 0 and key not in allowed_types:
            return api_resp(400, f"当前课程【{course}】不支持题型 {key}", {})

    section_row = query_one(
        f"SELECT section_title FROM question_bank WHERE course=%s AND section_no=%s AND {get_question_bank_non_template_where()} LIMIT 1",
        (course, section_no),
    )
    if not section_row:
        return api_resp(400, "题库中不存在该课程章节，请先导入题目数据", {})

    available_rows = query_all(
        f"""
        SELECT question_type, COUNT(*) AS total
        FROM question_bank
        WHERE course=%s AND section_no=%s AND {get_question_bank_non_template_where()}
        GROUP BY question_type
        """,
        (course, section_no),
    )
    available_map = {str(row.get("question_type")): int(row.get("total") or 0) for row in available_rows}

    shortage_items = []
    for question_type, required_count in type_counts.items():
        need = int(required_count or 0)
        if need <= 0:
            continue
        available = int(available_map.get(question_type) or 0)
        if available < need:
            shortage_items.append(
                {
                    "question_type": question_type,
                    "label": type_label_map.get(question_type, question_type),
                    "required": need,
                    "available": available,
                    "missing": need - available,
                }
            )

    if shortage_items:
        detail_text = "；".join(
            [
                f"{item['label']}需{item['required']}题，现有{item['available']}题"
                for item in shortage_items
            ]
        )
        return api_resp(
            400,
            f"题库题量不足：{course}第{section_no}节 {detail_text}。请先补充题目后再随机组卷。",
            {
                "course": course,
                "section_no": section_no,
                "shortage": shortage_items,
            },
        )

    generated_questions = []
    sort_no = 1
    for question_type, count in type_counts.items():
        if count <= 0:
            continue
        rows = query_all(
            f"""
            SELECT id, question_type, content, options_json, correct_answer, analysis, score
            FROM question_bank
            WHERE course=%s AND section_no=%s AND question_type=%s AND {get_question_bank_non_template_where()}
            ORDER BY RAND()
            LIMIT {count}
            """,
            (course, section_no, question_type),
        )
        if len(rows) < count:
            return api_resp(400, f"第{section_no}节的{question_type}题数量不足，请先补充题目", {})

        for row in rows:
            options = []
            if row.get("options_json"):
                try:
                    options = json.loads(row["options_json"])
                except Exception:
                    options = []
            generated_questions.append(
                {
                    "question_type": row["question_type"],
                    "content": row["content"],
                    "options": options,
                    "correct_answer": row.get("correct_answer"),
                    "analysis": row.get("analysis"),
                    "score": float(row.get("score") or 0),
                    "sort_no": sort_no,
                }
            )
            sort_no += 1

    count_desc_parts = []
    for key in ALL_QUESTION_TYPES:
        count_value = int(type_counts.get(key) or 0)
        if count_value > 0:
            count_desc_parts.append(f"{type_label_map[key]}{count_value}题")
    count_desc = "、".join(count_desc_parts)

    return api_resp(
        200,
        "生成成功",
        {
            "title": f"{course}第{section_no}节测验",
            "description": f"本次考试覆盖{course}第{section_no}节《{section_row['section_title']}》核心内容，题型构成为：{count_desc}，共{total_count}题。请在规定时间内完成作答并注意审题。",
            "duration_minutes": max(30, total_count * 8),
            "section_title": section_row["section_title"],
            "questions": generated_questions,
        },
    )


@app.post("/api/student/exam_retake_request")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_retake_request():
    """学员提交重考申请。"""
    payload = parse_json()
    validate_required(payload, ["exam_id", "reason"])

    exam_id = normalize_optional_int(payload.get("exam_id"), "exam_id", min_value=1)
    reason = mask_forbidden_text((payload.get("reason") or "").strip())
    if len(reason) < 5:
        return api_resp(400, "申请理由至少 5 个字", {})
    if len(reason) > 500:
        return api_resp(400, "申请理由不能超过 500 个字", {})

    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(403, "暂无可申请重考的考试", {})

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    exam_row = query_one(
        f"""
        SELECT id, teacher_id, title
        FROM exam
        WHERE id=%s AND teacher_id IN ({placeholders})
        LIMIT 1
        """,
        tuple([exam_id, *related_teacher_ids]),
    )
    if not exam_row:
        return api_resp(400, "考试不存在或无权限申请", {})

    record = query_one(
        "SELECT id FROM exam_record WHERE exam_id=%s AND student_id=%s LIMIT 1",
        (int(exam_id), int(current_user.id)),
    )
    if not record:
        return api_resp(400, "该考试尚未作答，不能申请重考", {})

    pending = query_one(
        """
        SELECT id
        FROM exam_retake_request
        WHERE exam_id=%s AND student_id=%s AND status='pending'
        ORDER BY id DESC
        LIMIT 1
        """,
        (int(exam_id), int(current_user.id)),
    )
    if pending:
        return api_resp(400, "已提交重考申请，请等待老师处理", {})

    request_id = insert_and_get_id(
        """
        INSERT INTO exam_retake_request (exam_id, student_id, teacher_id, reason, status)
        VALUES (%s, %s, %s, %s, 'pending')
        """,
        (int(exam_id), int(current_user.id), int(exam_row["teacher_id"]), reason),
    )

    create_notification(
        "user",
        title=f"重考申请：{exam_row['title']}",
        content=f"学员 {current_user.username} 提交了重考申请，请审核。",
        category="exam",
        level="warning",
        target_user_id=int(exam_row["teacher_id"]),
        action_path="/app/teacher/exam-manage",
    )

    return api_resp(200, "申请已提交", {"request_id": request_id})


@app.get("/api/teacher/exam_retake_requests")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_retake_requests():
    """老师查看重考申请列表。"""
    status = (request.args.get("status") or "all").strip()
    exam_id = normalize_optional_int(request.args.get("exam_id"), "exam_id", min_value=1)

    where_sql = ["r.teacher_id=%s"]
    params = [int(current_user.id)]
    if status in ["pending", "approved", "rejected"]:
        where_sql.append("r.status=%s")
        params.append(status)
    if exam_id is not None:
        where_sql.append("r.exam_id=%s")
        params.append(int(exam_id))

    rows = query_all(
        f"""
        SELECT
            r.id,
            r.exam_id,
            e.title AS exam_title,
            r.student_id,
            su.username AS student_username,
            r.reason,
            r.status,
            r.review_comment,
            r.review_time,
            r.create_time
        FROM exam_retake_request r
        JOIN exam e ON e.id = r.exam_id
        JOIN users su ON su.id = r.student_id
        WHERE {' AND '.join(where_sql)}
        ORDER BY FIELD(r.status, 'pending', 'approved', 'rejected'), r.id DESC
        """,
        tuple(params),
    )
    return api_resp(200, "查询成功", rows)


@app.put("/api/teacher/exam_retake_request/<int:request_id>/review")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_retake_request_review(request_id):
    """老师审核重考申请：同意/拒绝。"""
    payload = parse_json()
    action = (payload.get("action") or "").strip().lower()
    comment = mask_forbidden_text((payload.get("comment") or "").strip())
    if action not in ["approve", "reject"]:
        return api_resp(400, "action 非法，仅支持 approve/reject", {})
    if len(comment) > 500:
        return api_resp(400, "审核意见不能超过 500 个字", {})

    req_row = query_one(
        """
        SELECT r.id, r.exam_id, r.student_id, r.status, r.reason,
               e.title AS exam_title, su.username AS student_username
        FROM exam_retake_request r
        JOIN exam e ON e.id = r.exam_id
        JOIN users su ON su.id = r.student_id
        WHERE r.id=%s AND r.teacher_id=%s
        LIMIT 1
        """,
        (int(request_id), int(current_user.id)),
    )
    if not req_row:
        return api_resp(403, "无权审核该申请", {})
    if req_row.get("status") != "pending":
        return api_resp(400, "该申请已处理", {})

    next_status = "approved" if action == "approve" else "rejected"

    if next_status == "approved":
        execute(
            "DELETE FROM exam_record WHERE exam_id=%s AND student_id=%s",
            (int(req_row["exam_id"]), int(req_row["student_id"])),
        )

    execute(
        """
        UPDATE exam_retake_request
        SET status=%s, review_comment=%s, review_time=NOW()
        WHERE id=%s
        """,
        (next_status, comment or None, int(request_id)),
    )

    notify_title = f"重考申请已{'通过' if next_status == 'approved' else '拒绝'}：{req_row['exam_title']}"
    notify_content = (
        f"老师已同意你重考《{req_row['exam_title']}》，请在考试截止前重新作答。"
        if next_status == "approved"
        else f"老师已拒绝你重考《{req_row['exam_title']}》的申请。"
    )
    if comment:
        notify_content = f"{notify_content} 审核意见：{comment}"

    create_notification(
        "user",
        title=notify_title,
        content=notify_content,
        category="exam",
        level="info" if next_status == "approved" else "warning",
        target_user_id=int(req_row["student_id"]),
        action_path="/app/student/exam-center",
    )

    return api_resp(
        200,
        "审核完成",
        {
            "request_id": int(request_id),
            "status": next_status,
            "exam_id": int(req_row["exam_id"]),
            "student_id": int(req_row["student_id"]),
        },
    )


@app.get("/api/teacher/exam_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_list():
    """任课老师查看自己发布的考试列表。"""
    rows = query_all(
        """
        SELECT e.id, e.teacher_id, e.title, e.description, e.start_time, e.end_time,
               e.duration_minutes, e.status, e.create_time,
             COUNT(DISTINCT q.id) AS question_count,
             COUNT(DISTINCT er.id) AS submit_count,
             COUNT(DISTINCT er.student_id) AS student_count
        FROM exam e
        LEFT JOIN question q ON q.exam_id = e.id
        LEFT JOIN exam_record er ON er.exam_id = e.id
        WHERE e.teacher_id = %s
        GROUP BY e.id
        ORDER BY e.id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/teacher/exam/<int:exam_id>/detail")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_detail(exam_id):
    """任课老师查看单场考试详情与题目列表。"""
    exam_row = query_one(
        """
        SELECT e.id, e.teacher_id, e.title, e.description, e.start_time, e.end_time,
               e.duration_minutes, e.status, e.create_time,
               (
                   SELECT COUNT(*)
                   FROM question q2
                   WHERE q2.exam_id = e.id
               ) AS question_count,
               (
                   SELECT COUNT(*)
                   FROM exam_record er2
                   WHERE er2.exam_id = e.id
               ) AS submit_count,
               (
                   SELECT COUNT(DISTINCT er3.student_id)
                   FROM exam_record er3
                   WHERE er3.exam_id = e.id
               ) AS student_count
        FROM exam e
        WHERE e.id=%s AND e.teacher_id=%s
        """,
        (exam_id, int(current_user.id)),
    )
    if not exam_row:
        return api_resp(403, "只能查看自己发布的考试详情", {})

    question_rows = query_all(
        """
        SELECT id, question_type, content, options_json, correct_answer, analysis, score, sort_no
        FROM question
        WHERE exam_id=%s
        ORDER BY sort_no ASC, id ASC
        """,
        (exam_id,),
    )

    parsed_questions = []
    for row in question_rows:
        options = []
        if row.get("options_json"):
            try:
                options = json.loads(row["options_json"])
            except Exception:
                options = []
        parsed_questions.append(
            {
                "id": row["id"],
                "question_type": row["question_type"],
                "content": row["content"],
                "options": options,
                "correct_answer": row.get("correct_answer"),
                "analysis": row.get("analysis"),
                "score": row.get("score"),
                "sort_no": row.get("sort_no"),
            }
        )

    return api_resp(200, "查询成功", {"exam": exam_row, "questions": parsed_questions})


@app.delete("/api/teacher/exam/<int:exam_id>")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_delete(exam_id):
    """任课老师删除自己发布的考试。"""
    own = query_one(
        "SELECT id, title FROM exam WHERE id=%s AND teacher_id=%s",
        (exam_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能删除自己发布的考试", {})

    execute("DELETE FROM exam WHERE id=%s", (exam_id,))
    return api_resp(200, "删除成功", {"exam_id": exam_id, "title": own.get("title")})


@app.get("/api/teacher/exam/<int:exam_id>/records")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_records(exam_id):
    """任课老师查看考试提交记录。"""
    own = query_one("SELECT id FROM exam WHERE id=%s AND teacher_id=%s", (exam_id, int(current_user.id)))
    if not own:
        return api_resp(403, "只能查看自己考试的提交记录", {})

    rows = query_all(
        """
        SELECT er.id, er.exam_id, er.student_id, u.username AS student_username,
               er.auto_score, er.manual_score, er.total_score, er.status, er.submit_time
        FROM exam_record er
        JOIN users u ON u.id = er.student_id
        WHERE er.exam_id = %s
         ORDER BY er.total_score DESC, er.submit_time DESC
        """,
        (exam_id,),
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/teacher/exam_record/<int:record_id>/detail")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_record_detail(record_id):
    """任课老师查看单次考试记录答案详情。"""
    record = query_one(
        """
        SELECT er.id, er.exam_id, er.student_id, u.username AS student_username,
               er.auto_score, er.manual_score, er.total_score, er.status, er.submit_time
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        JOIN users u ON u.id = er.student_id
        WHERE er.id = %s AND e.teacher_id = %s
        """,
        (record_id, int(current_user.id)),
    )
    if not record:
        return api_resp(403, "只能查看自己考试的记录详情", {})

    answers = query_all(
        """
         SELECT a.id AS answer_id, a.question_id, q.question_type, q.content,
             q.correct_answer, q.analysis, q.score AS question_score,
               a.answer_text, a.is_correct, a.score_awarded
        FROM answer a
        JOIN question q ON q.id = a.question_id
        WHERE a.record_id = %s
        ORDER BY q.sort_no ASC, q.id ASC
        """,
        (record_id,),
    )
    return api_resp(200, "查询成功", {"record": record, "answers": answers})


@app.put("/api/teacher/exam_record/<int:record_id>/approve_retake")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_record_approve_retake(record_id):
    """老师同意学员重考：清除该学员本场考试记录（含答案），允许重新作答。"""
    record = query_one(
        """
        SELECT er.id, er.exam_id, er.student_id, e.title AS exam_title, u.username AS student_username
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        JOIN users u ON u.id = er.student_id
        WHERE er.id = %s AND e.teacher_id = %s
        """,
        (record_id, int(current_user.id)),
    )
    if not record:
        return api_resp(403, "只能操作自己考试的作答记录", {})

    execute("DELETE FROM exam_record WHERE id=%s", (record_id,))

    create_notification(
        "user",
        title=f"重考已批准：{record['exam_title']}",
        content=f"老师已同意你重考《{record['exam_title']}》，请在考试截止前重新作答。",
        category="exam",
        level="info",
        target_user_id=int(record["student_id"]),
        action_path="/app/student/exam-center",
    )

    return api_resp(
        200,
        "已同意重考",
        {
            "record_id": int(record_id),
            "exam_id": int(record["exam_id"]),
            "student_id": int(record["student_id"]),
            "student_username": record.get("student_username"),
            "exam_title": record.get("exam_title"),
        },
    )


@app.put("/api/teacher/exam_record/<int:record_id>/manual_grade")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_exam_record_manual_grade(record_id):
    """任课老师对考试记录进行主观题人工评分。"""
    payload = parse_json()
    grading_items = payload.get("grading_items")
    if not isinstance(grading_items, list) or not grading_items:
        raise ValidationError("grading_items 必须为非空数组")

    own = query_one(
        """
        SELECT er.id, er.auto_score
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        WHERE er.id = %s AND e.teacher_id = %s
        """,
        (record_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能评分自己考试的记录", {})

    for item in grading_items:
        if not isinstance(item, dict):
            continue
        answer_id = normalize_optional_int(item.get("answer_id"), "answer_id", min_value=1)
        score_awarded = float(item.get("score_awarded") or 0)
        if answer_id is None:
            continue
        if score_awarded < 0:
            raise ValidationError("score_awarded 不能小于 0")

        subjective_sql_list = ",".join(["%s"] * len(SUBJECTIVE_QUESTION_TYPES))
        target = query_one(
            f"""
            SELECT a.id
            FROM answer a
            JOIN question q ON q.id = a.question_id
            WHERE a.id=%s AND a.record_id=%s AND q.question_type IN ({subjective_sql_list})
            """,
            tuple([answer_id, record_id, *SUBJECTIVE_QUESTION_TYPES]),
        )
        if target:
            execute("UPDATE answer SET score_awarded=%s WHERE id=%s", (score_awarded, answer_id))

    subjective_sql_list = ",".join(["%s"] * len(SUBJECTIVE_QUESTION_TYPES))
    manual_sum_row = query_one(
        f"""
        SELECT COALESCE(SUM(a.score_awarded), 0) AS manual_sum
        FROM answer a
        JOIN question q ON q.id = a.question_id
        WHERE a.record_id = %s AND q.question_type IN ({subjective_sql_list})
        """,
        tuple([record_id, *SUBJECTIVE_QUESTION_TYPES]),
    )
    manual_sum = float((manual_sum_row or {}).get("manual_sum") or 0)
    auto_score = float((own or {}).get("auto_score") or 0)
    total_score = auto_score + manual_sum

    execute(
        "UPDATE exam_record SET manual_score=%s, total_score=%s, status='reviewed' WHERE id=%s",
        (manual_sum, total_score, record_id),
    )
    return api_resp(200, "人工评分完成", {"manual_score": manual_sum, "total_score": total_score})


@app.get("/api/student/exam_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_list():
    """学员查看考试列表。"""
    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(200, "查询成功", [])

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    rows = query_all(
        f"""
        SELECT e.id, e.title, e.description, e.start_time, e.end_time,
               e.duration_minutes, e.status,
               CASE
                   WHEN NOW() < e.start_time THEN 'not_started'
                   WHEN NOW() > e.end_time THEN 'ended'
                   ELSE 'ongoing'
               END AS exam_phase,
               CASE
                   WHEN NOW() >= e.start_time AND NOW() <= e.end_time THEN 1
                   ELSE 0
               END AS can_take_exam,
               CASE
                   WHEN er.id IS NOT NULL AND NOW() > e.end_time THEN 1
                   ELSE 0
               END AS can_view_analysis,
               rr.status AS retake_request_status,
               rr.review_comment AS retake_review_comment,
               rr.create_time AS retake_request_time,
               CASE
                   WHEN er.id IS NULL THEN 0
                   WHEN rr.status = 'pending' THEN 0
                   ELSE 1
               END AS can_request_retake,
               (
                   SELECT COUNT(*)
                   FROM question q2
                   WHERE q2.exam_id = e.id
               ) AS question_count,
               EXISTS(
                   SELECT 1
                   FROM question qs
                   WHERE qs.exam_id = e.id AND qs.question_type = 'short'
               ) AS has_short_question,
               er.id AS record_id,
               er.submit_time,
               er.total_score,
               er.status AS record_status,
               CASE
                   WHEN er.id IS NULL THEN 0
                   WHEN EXISTS(
                       SELECT 1
                       FROM question qs2
                       WHERE qs2.exam_id = e.id AND qs2.question_type = 'short'
                   ) AND er.status <> 'reviewed' THEN 0
                   ELSE 1
               END AS can_view_detail
        FROM exam e
        LEFT JOIN exam_record er ON er.exam_id = e.id AND er.student_id = %s
                LEFT JOIN exam_retake_request rr ON rr.id = (
                        SELECT r2.id
                        FROM exam_retake_request r2
                        WHERE r2.exam_id = e.id AND r2.student_id = %s
                        ORDER BY r2.id DESC
                        LIMIT 1
                )
        WHERE e.status IN ('published', 'closed')
          AND e.teacher_id IN ({placeholders})
        ORDER BY e.start_time DESC, e.id DESC
        """,
                tuple([int(current_user.id), int(current_user.id), *related_teacher_ids]),
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/student/exam/<int:exam_id>/detail")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_detail(exam_id):
    """学员查看考试详情与题目（作答前不返回标准答案）。"""
    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(403, "暂无可查看的考试", {})

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    exam_row = query_one(
        f"""
        SELECT id, teacher_id, title, description, start_time, end_time, duration_minutes, status
        FROM exam
        WHERE id=%s AND status IN ('published', 'closed')
          AND teacher_id IN ({placeholders})
        """,
        tuple([exam_id, *related_teacher_ids]),
    )
    if not exam_row:
        return api_resp(400, "考试不存在或未发布", {})

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exam_start_time = str(exam_row.get("start_time") or "")
    exam_end_time = str(exam_row.get("end_time") or "")
    if exam_start_time and now_str < exam_start_time:
        return api_resp(400, "考试未开始，暂不能作答", {})
    if exam_end_time and now_str > exam_end_time:
        return api_resp(400, "考试已截止，不能参加", {})

    questions = query_all(
        """
        SELECT id, question_type, content, options_json, analysis, score, sort_no
        FROM question
        WHERE exam_id = %s
        ORDER BY sort_no ASC, id ASC
        """,
        (exam_id,),
    )

    parsed_questions = []
    for item in questions:
        options = []
        if item.get("options_json"):
            try:
                options = json.loads(item["options_json"])
            except Exception:
                options = []
        parsed_questions.append(
            {
                "id": item["id"],
                "question_type": item["question_type"],
                "content": item["content"],
                "options": options,
                "analysis": item.get("analysis"),
                "score": item.get("score"),
                "sort_no": item.get("sort_no"),
            }
        )

    return api_resp(200, "查询成功", {"exam": exam_row, "questions": parsed_questions})


@app.post("/api/student/exam_submit")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_submit():
    """学员提交考试答案并执行自动判分。"""
    payload = parse_json()
    validate_required(payload, ["exam_id", "answers"])

    exam_id = normalize_optional_int(payload.get("exam_id"), "exam_id", min_value=1)
    answer_list = payload.get("answers")
    if not isinstance(answer_list, list):
        raise ValidationError("answers 必须为数组")

    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(403, "暂无可提交的考试", {})

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    exam_row = query_one(
        f"""
        SELECT id, teacher_id, title, status, start_time, end_time
        FROM exam
        WHERE id=%s AND status IN ('published', 'closed')
          AND teacher_id IN ({placeholders})
        """,
        tuple([exam_id, *related_teacher_ids]),
    )
    if not exam_row:
        return api_resp(400, "考试不存在或未发布", {})

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exam_start_time = str(exam_row.get("start_time") or "")
    exam_end_time = str(exam_row.get("end_time") or "")
    if exam_start_time and now_str < exam_start_time:
        return api_resp(400, "考试未开始，暂不能提交", {})
    if exam_end_time and now_str > exam_end_time:
        return api_resp(400, "考试已截止，不能提交", {})

    existing = query_one(
        "SELECT id FROM exam_record WHERE exam_id=%s AND student_id=%s",
        (exam_id, int(current_user.id)),
    )
    if existing:
        return api_resp(400, "该考试已提交，不能重复提交", {})

    question_rows = query_all(
        """
        SELECT id, question_type, correct_answer, score
        FROM question
        WHERE exam_id=%s
        ORDER BY sort_no ASC, id ASC
        """,
        (exam_id,),
    )
    if not question_rows:
        return api_resp(400, "该考试暂无题目", {})

    answer_map = {}
    for item in answer_list:
        if not isinstance(item, dict):
            continue
        qid = normalize_optional_int(item.get("question_id"), "question_id", min_value=1)
        if qid is None:
            continue
        answer_map[qid] = item.get("answer_text")

    auto_score = 0.0
    answer_payloads = []
    has_subjective_question = False
    for q in question_rows:
        question_id = q["id"]
        q_type = q["question_type"]
        if q_type in SUBJECTIVE_QUESTION_TYPES:
            has_subjective_question = True
        correct_answer = q.get("correct_answer")
        q_score = float(q.get("score") or 0)
        answer_text = answer_map.get(question_id)

        is_correct = None
        score_awarded = 0.0
        if q_type in OBJECTIVE_QUESTION_TYPES:
            if q_type == "multi":
                is_correct = 1 if normalize_multi_answer(answer_text) == normalize_multi_answer(correct_answer) else 0
            else:
                is_correct = 1 if normalize_answer_text(answer_text) == normalize_answer_text(correct_answer) else 0
            score_awarded = q_score if is_correct == 1 else 0.0
            auto_score += score_awarded

        answer_payloads.append(
            {
                "question_id": question_id,
                "answer_text": "" if answer_text is None else str(answer_text),
                "is_correct": is_correct,
                "score_awarded": score_awarded,
            }
        )

    record_status = "submitted" if has_subjective_question else "reviewed"
    record_id = insert_and_get_id(
        """
        INSERT INTO exam_record (exam_id, student_id, auto_score, manual_score, total_score, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (exam_id, int(current_user.id), auto_score, 0, auto_score, record_status),
    )

    for item in answer_payloads:
        insert_and_get_id(
            """
            INSERT INTO answer (record_id, question_id, answer_text, is_correct, score_awarded)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (record_id, item["question_id"], item["answer_text"], item["is_correct"], item["score_awarded"]),
        )

    pending_message = None
    if has_subjective_question:
        pending_message = "本次考试含主观题，需老师评分后才能查看成绩与详情"
        create_notification(
            "user",
            title=f"主观题待评分：{exam_row['title']}",
            content=f"学员 {current_user.username} 已提交考试《{exam_row['title']}》，请尽快完成主观题评分。",
            category="exam",
            level="warning",
            target_user_id=int(exam_row["teacher_id"]),
            action_path="/app/teacher/exam-manage",
        )
    else:
        create_notification(
            "user",
            title=f"考试已提交：{exam_row['title']}",
            content=f"学员 {current_user.username} 已完成考试《{exam_row['title']}》，系统已完成客观题自动判分。",
            category="exam",
            level="info",
            target_user_id=int(exam_row["teacher_id"]),
            action_path="/app/teacher/exam-manage",
        )

    create_notification(
        "role",
        title="考试提交动态",
        content=f"学员 {current_user.username} 已提交考试《{exam_row['title']}》。",
        category="exam",
        level="info",
        target_role="supervisor",
        action_path="/app/supervisor/dashboard",
    )

    return api_resp(
        200,
        "提交成功",
        {
            "record_id": record_id,
            "auto_score": auto_score,
            "record_status": record_status,
            "can_view_detail": 0 if has_subjective_question else 1,
            "pending_message": pending_message,
        },
    )


@app.get("/api/student/exam_record_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_record_list():
    """学员查看个人考试记录列表。"""
    rows = query_all(
        """
        SELECT er.id, er.exam_id, e.title AS exam_title,
               er.auto_score, er.manual_score, er.total_score, er.status, er.submit_time
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        WHERE er.student_id = %s
        ORDER BY er.submit_time DESC, er.id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/student/exam_record/<int:record_id>/detail")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_exam_record_detail(record_id):
    """学员查看单次考试记录详情。"""
    record = query_one(
        """
        SELECT er.id, er.exam_id, e.title AS exam_title, e.end_time,
               er.auto_score, er.manual_score, er.total_score, er.status, er.submit_time
        FROM exam_record er
        JOIN exam e ON e.id = er.exam_id
        WHERE er.id=%s AND er.student_id=%s
        """,
        (record_id, int(current_user.id)),
    )
    if not record:
        return api_resp(400, "记录不存在", {})

    end_time_text = str(record.get("end_time") or "")
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    can_view_analysis = 1 if end_time_text and now_text > end_time_text else 0

    rows = query_all(
        """
         SELECT a.id AS answer_id, a.question_id, q.question_type, q.content, q.correct_answer,
             q.analysis, a.answer_text, a.is_correct, a.score_awarded, q.score AS question_score
        FROM answer a
        JOIN question q ON q.id = a.question_id
        WHERE a.record_id = %s
        ORDER BY q.sort_no ASC, q.id ASC
        """,
        (record_id,),
    )

    masked_rows = []
    for row in rows:
        row_copy = dict(row)
        if not can_view_analysis:
            row_copy["correct_answer"] = None
            row_copy["analysis"] = None
        masked_rows.append(row_copy)

    record["can_view_analysis"] = int(can_view_analysis)
    return api_resp(200, "查询成功", {"record": record, "answers": masked_rows})


@app.get("/api/notification/list")
@login_required
@role_required("student", "teacher", "supervisor")
@handle_errors("数据库操作失败")
def notification_list():
    """普通用户通知列表。"""
    category = (request.args.get("category") or "all").strip()
    rows = get_user_notification_list(int(current_user.id), current_user.role, category=category)
    unread_count = sum(1 for item in rows if not item.get("is_read"))
    return api_resp(200, "查询成功", {"list": rows, "unread_count": unread_count})


@app.post("/api/notification/<int:notification_id>/read")
@login_required
@role_required("student", "teacher", "supervisor")
@handle_errors("数据库操作失败")
def notification_mark_read(notification_id):
    """普通用户标记单条通知为已读。"""
    rows = get_user_notification_list(int(current_user.id), current_user.role)
    if not any(int(item["id"]) == notification_id for item in rows):
        return api_resp(403, "无权操作该通知", {})

    mark_notification_read(notification_id, "user", int(current_user.id))
    return api_resp(200, "标记成功", {})


@app.post("/api/notification/read_all")
@login_required
@role_required("student", "teacher", "supervisor")
@handle_errors("数据库操作失败")
def notification_mark_all_read():
    """普通用户标记全部通知为已读。"""
    rows = get_user_notification_list(int(current_user.id), current_user.role)
    for item in rows:
        if not item.get("is_read"):
            mark_notification_read(int(item["id"]), "user", int(current_user.id))
    return api_resp(200, "全部标记成功", {})


@app.get("/api/admin/notification/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_notification_list():
    """管理员通知列表。"""
    admin_id = int(session.get("admin_id"))
    category = (request.args.get("category") or "all").strip()
    rows = get_admin_notification_list(admin_id, category=category)
    unread_count = sum(1 for item in rows if not item.get("is_read"))
    return api_resp(200, "查询成功", {"list": rows, "unread_count": unread_count})


@app.post("/api/admin/notification/<int:notification_id>/read")
@admin_required
@handle_errors("数据库操作失败")
def admin_notification_mark_read(notification_id):
    """管理员标记单条通知为已处理。"""
    admin_id = int(session.get("admin_id"))
    rows = get_admin_notification_list(admin_id)
    if not any(int(item["id"]) == notification_id for item in rows):
        return api_resp(403, "无权操作该通知", {})

    mark_notification_read(notification_id, "admin", admin_id)
    return api_resp(200, "标记成功", {})


@app.post("/api/admin/notification/read_all")
@admin_required
@handle_errors("数据库操作失败")
def admin_notification_mark_all_read():
    """管理员标记全部通知为已处理。"""
    admin_id = int(session.get("admin_id"))
    rows = get_admin_notification_list(admin_id)
    for item in rows:
        if not item.get("is_read"):
            mark_notification_read(int(item["id"]), "admin", admin_id)
    return api_resp(200, "全部标记成功", {})


def extract_recommendation_keywords(text_list, max_count=8):
    """从历史弱项文本中提取简易关键词。"""
    stop_words = {
        "今天", "明天", "完成", "复习", "学习", "计划", "任务", "内容", "老师", "同学", "问题", "进行", "已经", "需要",
        "and", "the", "for", "with", "from", "this", "that",
    }

    scores = {}
    for text in text_list:
        if not text:
            continue
        tokens = re.split(r"[^\u4e00-\u9fffA-Za-z0-9]+", str(text).strip().lower())
        for token in tokens:
            token = token.strip()
            if len(token) < 2:
                continue
            if token in stop_words:
                continue
            scores[token] = scores.get(token, 0) + 1

    if not scores:
        return ["基础", "真题", "错题", "高频"]

    sorted_tokens = sorted(scores.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [item[0] for item in sorted_tokens[:max_count]]


def score_text_by_keywords(text, keywords):
    if not text:
        return 0, []
    source = str(text).lower()
    hit_keywords = []
    score = 0
    for keyword in keywords:
        if keyword and keyword in source:
            score += 3
            hit_keywords.append(keyword)
    return score, hit_keywords


def detect_material_course(material_title, teacher_course=None):
    if teacher_course:
        return str(teacher_course)

    title = str(material_title or "")
    rule_map = [
        ("西医临床", ["西医", "内科", "外科", "生理", "病理", "诊断", "临床"]),
        ("中医临床", ["中医", "方剂", "针灸", "辨证", "伤寒", "中药"]),
        ("口腔医学", ["口腔", "牙", "龋", "牙周", "修复", "根管"]),
        ("政治", ["政治", "马原", "毛概", "史纲", "思修", "时政"]),
        ("英语", ["英语", "阅读", "翻译", "写作", "完形", "长难句"]),
        ("其他类（护理学、医学技术、基础医学、公共卫生等）", ["护理", "公共卫生", "统计", "检验", "影像", "基础医学"]),
    ]
    for course_name, tokens in rule_map:
        if any(token in title for token in tokens):
            return course_name
    return "医学考研综合"


def build_exam_oriented_reason(hit_keywords, weak_review_count, weak_exam_count, todo_learning_count, download_count, material_title=None, teacher_course=None):
    """生成更符合考研备考语境的推荐原因。"""
    course_name = detect_material_course(material_title, teacher_course=teacher_course)

    course_focus_map = {
        "西医临床": "贴合西医临床综合命题路径，适合按系统高频考点做强化",
        "中医临床": "聚焦辨证论治与方药配伍，适合中医综合主观题组织",
        "口腔医学": "围绕口腔高频疾病与诊疗流程，适合临床场景化复习",
        "政治": "贴合政治主观题采分点，适合背诵框架与时政联动",
        "英语": "围绕阅读与写作提分关键，适合题型化训练与复盘",
        "其他类（护理学、医学技术、基础医学、公共卫生等）": "覆盖护理与公卫等综合基础，适合跨章节查漏补缺",
        "医学考研综合": "贴合医学考研综合复习节奏，适合作为阶段巩固资料",
    }

    focus_reason = course_focus_map.get(course_name, course_focus_map["医学考研综合"])

    stage_reason = None
    if weak_exam_count >= 3:
        stage_reason = "针对近期错题薄弱点，建议优先做专题突破"
    elif weak_review_count >= 3:
        stage_reason = "复习薄弱项较多，建议结合本资料做章节回炉"
    elif todo_learning_count >= 3:
        stage_reason = "当前待办任务较多，建议先用本资料梳理主干框架"
    else:
        stage_reason = "适合作为阶段巩固资料，提升考研答题稳定性"

    keyword_reason = None
    if hit_keywords:
        keyword_reason = f"匹配你的考研关键词：{'、'.join(hit_keywords[:3])}"

    heat_reason = None
    if int(download_count or 0) >= 20:
        heat_reason = "历届学员高频下载，适合考前强化"
    else:
        heat_reason = "与当前复习节奏匹配，可用于查漏补缺"

    parts = [focus_reason, stage_reason]
    if keyword_reason:
        parts.append(keyword_reason)
    parts.append(heat_reason)
    return "；".join(parts)


@app.get("/api/student/recommendation_feed")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_recommendation_feed():
    """基于学习行为与错题记录返回资源推荐。"""
    student_id = int(current_user.id)
    related_teacher_ids = get_student_related_teacher_ids(student_id)

    weak_exam_rows = query_all(
                f"""
        SELECT q.content
        FROM answer a
        JOIN exam_record er ON er.id = a.record_id
        JOIN question q ON q.id = a.question_id
        WHERE er.student_id = %s
          AND (
                        (q.question_type IN ({','.join(["'%s'" % t for t in OBJECTIVE_QUESTION_TYPES])}) AND a.is_correct = 0)
                        OR (q.question_type IN ({','.join(["'%s'" % t for t in SUBJECTIVE_QUESTION_TYPES])}) AND a.score_awarded < q.score)
          )
        ORDER BY er.submit_time DESC, a.id DESC
        LIMIT 30
        """,
        (student_id,),
    )

    todo_learning_rows = query_all(
        """
        SELECT lt.task_title
        FROM learning_task lt
        JOIN learning_plan lp ON lp.id = lt.plan_id
        WHERE lp.student_id = %s
          AND lt.is_done = 0
        ORDER BY lt.task_date ASC, lt.id ASC
        LIMIT 30
        """,
        (student_id,),
    )

    keyword_texts = []
    for row in weak_exam_rows:
        keyword_texts.append(row.get("content"))
    for row in todo_learning_rows:
        keyword_texts.append(row.get("task_title"))

    keywords = extract_recommendation_keywords(keyword_texts)

    material_rows = []
    if related_teacher_ids:
        placeholders = ", ".join(["%s"] * len(related_teacher_ids))
        material_rows = query_all(
            f"""
            SELECT m.id, m.title, m.file_path, m.video_url, m.download_count, m.upload_time,
                   m.teacher_id,
                   u.username AS teacher_name,
                   tcb.course AS teacher_course
            FROM materials m
            LEFT JOIN users u ON u.id = m.teacher_id
            LEFT JOIN teacher_course_binding tcb ON tcb.teacher_id = m.teacher_id
            WHERE m.teacher_id IN ({placeholders})
            ORDER BY m.upload_time DESC, m.id DESC
            LIMIT 300
            """,
            tuple(related_teacher_ids),
        )

    scored_materials = []
    for row in material_rows:
        score, hit_keywords = score_text_by_keywords(row.get("title"), keywords)
        score += min(int(row.get("download_count") or 0) // 5, 4)
        reason = build_exam_oriented_reason(
            hit_keywords,
            0,
            len(weak_exam_rows),
            len(todo_learning_rows),
            int(row.get("download_count") or 0),
            material_title=row.get("title"),
            teacher_course=row.get("teacher_course"),
        )
        scored_materials.append({**row, "recommend_score": score, "reason": reason})

    scored_materials.sort(key=lambda item: (-item["recommend_score"], -(item.get("download_count") or 0), -(item.get("id") or 0)))
    recommended_materials = scored_materials[:5]

    return api_resp(
        200,
        "查询成功",
        {
            "keywords": keywords,
            "materials": recommended_materials,
            "summary": {
                "weak_review_count": 0,
                "weak_exam_count": len(weak_exam_rows),
                "todo_learning_count": len(todo_learning_rows),
            },
        },
    )


# ==============================
# 作业接口
# ==============================
@app.post("/api/teacher/publish_homework")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def publish_homework():
    """
    任课老师发布作业。
    必填：title、deadline（YYYY-MM-DD HH:MM:SS）
    """
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        title = mask_forbidden_text((request.form.get("title") or "").strip())
        content = mask_forbidden_text((request.form.get("content") or "").strip())
        deadline = (request.form.get("deadline") or "").strip()
    else:
        payload = parse_json()
        title = mask_forbidden_text((payload.get("title") or "").strip())
        content = mask_forbidden_text((payload.get("content") or "").strip())
        deadline = (payload.get("deadline") or "").strip()
        validate_required(payload, ["title", "deadline"])

    if not title or not deadline:
        raise ValidationError("title 和 deadline 为必填项")
    if len(title) > 100:
        raise ValidationError("title 长度不能超过 100")

    if not is_valid_datetime(deadline):
        return api_resp(400, "deadline 格式错误，应为 YYYY-MM-DD HH:MM:SS", {})

    file_path = None
    file_obj = request.files.get("file") if is_multipart else None
    if file_obj and file_obj.filename:
        saved_name = save_upload_file(file_obj, HOMEWORK_DIR)
        file_path = f"homework/{saved_name}"

    homework_id = insert_and_get_id(
        """
        INSERT INTO homework (teacher_id, title, content, file_path, publish_time, deadline)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            int(current_user.id),
            title,
            content,
            file_path,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            deadline,
        ),
    )

    bound_course = resolve_teacher_bound_course(int(current_user.id))
    if bound_course in ["政治", "英语"]:
        student_rows = query_all("SELECT user_id FROM student_info")
    else:
        student_rows = query_all("SELECT user_id FROM student_info WHERE teacher_id=%s", (int(current_user.id),))
    for row in student_rows:
        create_notification(
            "user",
            title=f"新作业发布：{title}",
            content=f"老师 {current_user.username} 发布了新作业，请在截止时间前完成提交。",
            category="homework",
            level="warning",
            target_user_id=int(row["user_id"]),
            action_path="/app/student/homework",
        )

    create_notification(
        "admin",
        title="新增作业发布",
        content=f"教师 {current_user.username} 发布了作业《{title}》。",
        category="homework",
        level="warning",
        action_path="/admin/homework",
    )

    return api_resp(200, "发布成功", {"homework_id": homework_id, "file_path": file_path})


@app.get("/api/teacher/homework_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_homework_list():
    """任课老师查看自己发布的作业。"""
    rows = query_all(
        """
        SELECT id, teacher_id, title, content, file_path, publish_time, deadline
        FROM homework
        WHERE teacher_id = %s
        ORDER BY id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.put("/api/teacher/homework/<int:homework_id>")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_homework_update(homework_id):
    """任课老师修改（批改）自己已发布的作业。"""
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        title = mask_forbidden_text((request.form.get("title") or "").strip())
        content = mask_forbidden_text((request.form.get("content") or "").strip())
        deadline = (request.form.get("deadline") or "").strip()
        clear_file = str(request.form.get("clear_file") or "0").lower() in ("1", "true", "yes")
    else:
        payload = parse_json()
        title = mask_forbidden_text((payload.get("title") or "").strip())
        content = mask_forbidden_text((payload.get("content") or "").strip())
        deadline = (payload.get("deadline") or "").strip()
        clear_file = bool(payload.get("clear_file"))
        validate_required(payload, ["title", "deadline"])

    if not title or not deadline:
        raise ValidationError("title 和 deadline 为必填项")
    if len(title) > 100:
        raise ValidationError("title 长度不能超过 100")
    if not is_valid_datetime(deadline):
        return api_resp(400, "deadline 格式错误，应为 YYYY-MM-DD HH:MM:SS", {})

    target = query_one(
        "SELECT id, file_path FROM homework WHERE id=%s AND teacher_id=%s",
        (homework_id, int(current_user.id)),
    )
    if not target:
        return api_resp(403, "只能修改自己发布的作业", {})

    old_relative_path = target.get("file_path")
    next_file_path = old_relative_path

    new_file_obj = request.files.get("file") if is_multipart else None
    if new_file_obj and new_file_obj.filename:
        saved_name = save_upload_file(new_file_obj, HOMEWORK_DIR)
        next_file_path = f"homework/{saved_name}"

        if old_relative_path:
            old_abs_path = os.path.join(UPLOAD_DIR, old_relative_path)
            if os.path.exists(old_abs_path):
                try:
                    os.remove(old_abs_path)
                except OSError:
                    app.logger.warning("删除旧作业附件失败：%s", old_abs_path)
    elif clear_file and old_relative_path:
        next_file_path = None
        old_abs_path = os.path.join(UPLOAD_DIR, old_relative_path)
        if os.path.exists(old_abs_path):
            try:
                os.remove(old_abs_path)
            except OSError:
                app.logger.warning("删除作业附件失败：%s", old_abs_path)

    execute(
        "UPDATE homework SET title=%s, content=%s, file_path=%s, deadline=%s WHERE id=%s",
        (title, content, next_file_path, deadline, homework_id),
    )
    return api_resp(200, "作业更新成功", {"file_path": next_file_path})


@app.delete("/api/teacher/homework/<int:homework_id>")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_homework_delete(homework_id):
    """任课老师删除自己发布的作业。"""
    own = query_one(
        "SELECT id FROM homework WHERE id=%s AND teacher_id=%s",
        (homework_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能删除自己发布的作业", {})

    execute("DELETE FROM homework WHERE id=%s", (homework_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/teacher/homework_submission_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_homework_submission_list():
    """任课老师查看自己作业的学员提交列表。"""
    homework_id = normalize_optional_int(request.args.get("homework_id"), "homework_id", min_value=1)

    conditions = ["h.teacher_id = %s"]
    params = [int(current_user.id)]
    if homework_id is not None:
        conditions.append("hs.homework_id = %s")
        params.append(homework_id)

    rows = query_all(
        f"""
        SELECT hs.id, hs.homework_id, h.title AS homework_title, h.deadline AS homework_deadline,
               hs.student_id, su.username AS student_username,
               hs.content, hs.file_path, hs.score, hs.feedback,
               hs.submit_time, hs.update_time
        FROM homework_submission hs
        JOIN homework h ON hs.homework_id = h.id
        JOIN users su ON hs.student_id = su.id
        WHERE {' AND '.join(conditions)}
        ORDER BY hs.submit_time DESC, hs.id DESC
        """,
        tuple(params),
    )
    return api_resp(200, "查询成功", rows)


@app.put("/api/teacher/homework_submission/<int:submission_id>/review")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_homework_submission_review(submission_id):
    """任课老师对作业提交进行评分与评语。"""
    payload = parse_json()
    score = normalize_optional_int(payload.get("score"), "score", min_value=0, max_value=100)
    feedback = (payload.get("feedback") or "").strip() or None

    own = query_one(
        """
        SELECT hs.id
        FROM homework_submission hs
        JOIN homework h ON hs.homework_id = h.id
        WHERE hs.id=%s AND h.teacher_id=%s
        """,
        (submission_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能评分自己作业的提交记录", {})

    execute(
        "UPDATE homework_submission SET score=%s, feedback=%s WHERE id=%s",
        (score, feedback, submission_id),
    )
    return api_resp(200, "评分成功", {})


@app.get("/api/student/homework_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_homework_list():
    """
    学员查看作业列表。
    优先仅展示与本人已关联老师相关的作业，避免无关课程混入。
    """
    relevant_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not relevant_teacher_ids:
        return api_resp(200, "查询成功", [])

    params = [int(current_user.id)]
    placeholders = ", ".join(["%s"] * len(relevant_teacher_ids))
    filter_sql = f"WHERE h.teacher_id IN ({placeholders})"
    params.extend(relevant_teacher_ids)

    rows = query_all(
        f"""
        SELECT h.id, h.teacher_id, t.username AS teacher_name,
             h.title, h.content, h.file_path AS homework_file_path, h.publish_time, h.deadline,
               hs.id AS submission_id,
               hs.content AS submission_content,
               hs.file_path AS submission_file_path,
               hs.score AS submission_score,
               hs.feedback AS submission_feedback,
               hs.submit_time AS submission_time
        FROM homework h
        LEFT JOIN users t ON h.teacher_id = t.id
        LEFT JOIN homework_submission hs
               ON hs.homework_id = h.id AND hs.student_id = %s
         {filter_sql}
        ORDER BY h.publish_time DESC
         """,
         tuple(params),
    )
    return api_resp(200, "查询成功", rows)


@app.post("/api/student/homework_submit")
@login_required
@role_required("student")
@handle_errors("文件上传或数据库操作失败")
def student_homework_submit():
    """学员提交作业（同一作业每人一条记录，可重复提交覆盖）。"""
    homework_id = normalize_optional_int(request.form.get("homework_id"), "homework_id", min_value=1)
    content = mask_forbidden_text((request.form.get("content") or "").strip())
    file_obj = request.files.get("file")

    if homework_id is None:
        return api_resp(400, "缺少 homework_id", {})

    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(403, "暂无可提交的作业", {})

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    homework = query_one(
        f"SELECT id, teacher_id, title, deadline FROM homework WHERE id=%s AND teacher_id IN ({placeholders})",
        tuple([homework_id, *related_teacher_ids]),
    )
    if not homework:
        return api_resp(400, "作业不存在或不在当前学习范围内", {})

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    homework_deadline = str(homework.get("deadline") or "")
    if homework_deadline and now_str > homework_deadline:
        return api_resp(400, "作业已过截止时间，不能提交", {})

    file_path = None
    if file_obj and file_obj.filename:
        saved_name = save_upload_file(file_obj, MATERIALS_DIR)
        file_path = f"materials/{saved_name}"

    existing = query_one(
        "SELECT id, file_path FROM homework_submission WHERE homework_id=%s AND student_id=%s",
        (homework_id, int(current_user.id)),
    )
    if existing:
        if file_path:
            execute(
                """
                UPDATE homework_submission
                SET content=%s, file_path=%s, submit_time=%s
                WHERE id=%s
                """,
                (content, file_path, now_str, existing["id"]),
            )
        else:
            execute(
                """
                UPDATE homework_submission
                SET content=%s, submit_time=%s
                WHERE id=%s
                """,
                (content, now_str, existing["id"]),
            )
        create_notification(
            "user",
            title=f"作业已更新：{homework['title']}",
            content=f"学员 {current_user.username} 更新了作业提交，请及时查看。",
            category="homework",
            level="info",
            target_user_id=int(homework["teacher_id"]),
            action_path="/app/teacher/publish-homework",
        )
        create_notification(
            "role",
            title="作业提交通知",
            content=f"学员 {current_user.username} 更新了作业《{homework['title']}》提交。",
            category="homework",
            level="info",
            target_role="supervisor",
            action_path="/app/supervisor/dashboard",
        )
        return api_resp(200, "提交已更新", {"submission_id": existing["id"]})

    submission_id = insert_and_get_id(
        """
        INSERT INTO homework_submission (homework_id, student_id, content, file_path, submit_time)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (homework_id, int(current_user.id), content, file_path, now_str),
    )

    create_notification(
        "user",
        title=f"新作业提交：{homework['title']}",
        content=f"学员 {current_user.username} 已提交作业，请及时批改。",
        category="homework",
        level="warning",
        target_user_id=int(homework["teacher_id"]),
        action_path="/app/teacher/publish-homework",
    )
    create_notification(
        "role",
        title="作业提交通知",
        content=f"学员 {current_user.username} 提交了作业《{homework['title']}》。",
        category="homework",
        level="info",
        target_role="supervisor",
        action_path="/app/supervisor/dashboard",
    )
    return api_resp(200, "提交成功", {"submission_id": submission_id})


# ==============================
# 资料接口
# ==============================
@app.post("/api/teacher/upload_materials")
@login_required
@role_required("teacher")
@handle_errors("文件上传或数据库操作失败")
def upload_materials():
    """
    任课老师上传学习资料。
    入参：multipart/form-data
      - title: 资料标题
      - file: 文件
    """
    title = mask_forbidden_text((request.form.get("title") or "").strip())
    video_url = normalize_optional_video_url(request.form.get("video_url"))
    file_obj = request.files.get("file")

    if not title or not file_obj:
        return api_resp(400, "title 和 file 不能为空", {})

    if len(title) > 100:
        return api_resp(400, "资料标题长度不能超过 100 个字符", {})

    saved_name = save_upload_file(file_obj, MATERIALS_DIR)
    relative_path = f"materials/{saved_name}"

    material_id = insert_and_get_id(
        """
        INSERT INTO materials (teacher_id, title, file_path, video_url, upload_time, download_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            int(current_user.id),
            title,
            relative_path,
            video_url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            0,
        ),
    )

    teacher_course = resolve_teacher_bound_course(int(current_user.id))
    is_public_course = teacher_course in ["政治", "英语"]
    if is_public_course:
        student_rows = query_all("SELECT user_id FROM student_info")
    else:
        student_rows = query_all("SELECT user_id FROM student_info WHERE teacher_id=%s", (int(current_user.id),))
    for row in student_rows:
        create_notification(
            "user",
            title=f"新资料上架：{title}",
            content=f"老师 {current_user.username} 上传了新的学习资料，建议尽快查看。",
            category="materials",
            level="info",
            target_user_id=int(row["user_id"]),
            action_path="/app/student/materials",
        )

    create_notification(
        "admin",
        title="新增学习资料",
        content=f"教师 {current_user.username} 上传了资料《{title}》。",
        category="materials",
        level="info",
        action_path="/admin/materials",
    )

    return api_resp(200, "上传成功", {"material_id": material_id, "file_path": relative_path})


@app.get("/api/teacher/materials_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_materials_list():
    """任课老师查看自己上传的资料列表。"""
    rows = query_all(
        """
        SELECT id, teacher_id, title, file_path, video_url, upload_time, download_count
        FROM materials
        WHERE teacher_id = %s
        ORDER BY id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.put("/api/teacher/materials/<int:material_id>")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_materials_update(material_id):
    """任课老师修改自己上传的资料。"""
    title = ""
    file_obj = None
    video_url = None

    content_type = (request.content_type or "").lower()
    if "multipart/form-data" in content_type or request.form:
        title = mask_forbidden_text((request.form.get("title") or "").strip())
        video_url = normalize_optional_video_url(request.form.get("video_url"))
        file_obj = request.files.get("file")
    else:
        payload = parse_json()
        title = mask_forbidden_text((payload.get("title") or "").strip())
        video_url = normalize_optional_video_url(payload.get("video_url"))

    if not title:
        return api_resp(400, "title 不能为空", {})
    if len(title) > 100:
        return api_resp(400, "资料标题长度不能超过 100 个字符", {})

    own = query_one(
        "SELECT id, file_path FROM materials WHERE id=%s AND teacher_id=%s",
        (material_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能修改自己上传的资料", {})

    if file_obj:
        saved_name = save_upload_file(file_obj, MATERIALS_DIR)
        new_relative_path = f"materials/{saved_name}"

        execute(
            "UPDATE materials SET title=%s, file_path=%s, video_url=%s WHERE id=%s",
            (title, new_relative_path, video_url, material_id),
        )

        old_relative_path = (own.get("file_path") or "").strip()
        if old_relative_path.startswith("materials/"):
            old_abs_path = os.path.join(UPLOAD_DIR, old_relative_path)
            if os.path.isfile(old_abs_path):
                try:
                    os.remove(old_abs_path)
                except OSError:
                    app.logger.warning("旧资料文件删除失败: %s", old_abs_path)
    else:
        execute("UPDATE materials SET title=%s, video_url=%s WHERE id=%s", (title, video_url, material_id))

    return api_resp(200, "更新成功", {})


@app.delete("/api/teacher/materials/<int:material_id>")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_materials_delete(material_id):
    """任课老师删除自己上传的资料。"""
    own = query_one("SELECT id FROM materials WHERE id=%s AND teacher_id=%s", (material_id, int(current_user.id)))
    if not own:
        return api_resp(403, "只能删除自己上传的资料", {})

    execute("DELETE FROM materials WHERE id=%s", (material_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/student/materials_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_materials_list():
    """学员查看资料列表。"""
    pinned_titles = [
        "政治-近代史时间轴梳理",
        "英语-阅读长难句拆分示例",
        "西医临床系统复习讲义（循环+呼吸）（第1版）",
        "英语阅读同义替换与长难句拆解（第1版）",
    ]
    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(200, "查询成功", [])

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    rows = query_all(
        f"""
        SELECT m.id, m.teacher_id, u.username AS teacher_name,
             m.title, m.file_path, m.video_url, m.upload_time, m.download_count
        FROM materials m
        LEFT JOIN users u ON m.teacher_id = u.id
        WHERE m.teacher_id IN ({placeholders})
        ORDER BY
            CASE
                WHEN m.title = %s THEN 0
                WHEN m.title = %s THEN 1
                WHEN m.title = %s THEN 2
                WHEN m.title = %s THEN 3
                ELSE 9
            END ASC,
            m.upload_time DESC,
            m.id DESC
        """,
        tuple([*related_teacher_ids, *pinned_titles]),
    )
    return api_resp(200, "查询成功", rows)


@app.post("/api/student/download_materials")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def download_materials():
    """
    学员下载资料并统计下载次数。

    核心逻辑：
    1) 按 material_id 查找资料
    2) 下载次数 +1
    3) 返回文件访问地址
    """
    payload = parse_json()
    material_id = payload.get("material_id")
    if not material_id:
        return api_resp(400, "缺少 material_id", {})

    related_teacher_ids = get_student_related_teacher_ids(int(current_user.id))
    if not related_teacher_ids:
        return api_resp(403, "暂无可下载的资料", {})

    placeholders = ", ".join(["%s"] * len(related_teacher_ids))
    material = query_one(
        f"SELECT id, title, file_path, video_url, download_count FROM materials WHERE id = %s AND teacher_id IN ({placeholders})",
        tuple([material_id, *related_teacher_ids]),
    )
    if not material:
        return api_resp(400, "资料不存在或不在当前学习范围内", {})

    # 关键逻辑：下载统计 +1
    execute(
        "UPDATE materials SET download_count = download_count + 1 WHERE id = %s",
        (material_id,),
    )

    latest = query_one(
        "SELECT id, title, file_path, video_url, download_count FROM materials WHERE id = %s",
        (material_id,),
    )

    return api_resp(
        200,
        "下载记录成功",
        {
            "material_id": latest["id"],
            "title": latest["title"],
            "file_path": latest["file_path"],
            "video_url": latest.get("video_url"),
            "download_count": latest["download_count"],
            "download_url": f"/uploads/{latest['file_path']}",
        },
    )


# ==============================
# 打卡接口
# ==============================
@app.post("/api/student/checkin")
@login_required
@role_required("student")
@handle_errors("文件上传或数据库操作失败")
def student_checkin():
    """
    学员打卡（每日仅 1 次）。

    核心逻辑：
    - 先查当天是否已打卡
    - 若已打卡则拒绝
    - 否则写入打卡记录
    """
    content = mask_forbidden_text((request.form.get("content") or "").strip())
    checkin_date = (request.form.get("checkin_date") or date.today().strftime("%Y-%m-%d")).strip()
    file_obj = request.files.get("file")

    if not is_valid_date(checkin_date):
        return api_resp(400, "checkin_date 格式错误，应为 YYYY-MM-DD", {})

    # 关键逻辑：每日仅 1 次打卡校验
    exists = query_one(
        "SELECT id FROM checkin WHERE student_id = %s AND checkin_date = %s",
        (int(current_user.id), checkin_date),
    )
    if exists:
        return api_resp(400, "今日已打卡，不能重复打卡", {})

    relative_path = None
    if file_obj and file_obj.filename:
        saved_name = save_upload_file(file_obj, CHECKIN_DIR)
        relative_path = f"checkin/{saved_name}"

    checkin_id = insert_and_get_id(
        """
        INSERT INTO checkin (student_id, content, file_path, checkin_date, create_time)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            int(current_user.id),
            content,
            relative_path,
            checkin_date,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    profile = get_student_profile_and_primary_teacher(int(current_user.id))
    if profile.get("teacher_id"):
        create_notification(
            "user",
            title="学员已打卡",
            content=f"学员 {profile.get('student_name') or current_user.username} 完成了 {checkin_date} 的学习打卡。",
            category="checkin",
            level="info",
            target_user_id=int(profile["teacher_id"]),
            action_path="/app/teacher/dashboard",
        )
    create_notification(
        "role",
        title="打卡动态提醒",
        content=f"学员 {profile.get('student_name') or current_user.username} 新增了一条学习打卡。",
        category="checkin",
        level="info",
        target_role="supervisor",
        action_path="/app/supervisor/checkin-stat",
    )

    return api_resp(200, "打卡成功", {"checkin_id": checkin_id, "file_path": relative_path})


@app.put("/api/student/checkin/<int:checkin_id>")
@login_required
@role_required("student")
@handle_errors("文件上传或数据库操作失败")
def student_checkin_update(checkin_id):
    """学员编辑自己的打卡记录。"""
    own = query_one("SELECT id, student_id FROM checkin WHERE id=%s", (checkin_id,))
    if not own or int(own["student_id"]) != int(current_user.id):
        return api_resp(403, "只能编辑自己的打卡记录", {})

    content = mask_forbidden_text((request.form.get("content") or "").strip())
    checkin_date = (request.form.get("checkin_date") or "").strip()
    if not checkin_date or not is_valid_date(checkin_date):
        return api_resp(400, "checkin_date 格式错误，应为 YYYY-MM-DD", {})

    conflict = query_one(
        "SELECT id FROM checkin WHERE student_id=%s AND checkin_date=%s AND id<>%s",
        (int(current_user.id), checkin_date, checkin_id),
    )
    if conflict:
        return api_resp(400, "该日期已存在打卡记录", {})

    file_obj = request.files.get("file")
    if file_obj and file_obj.filename:
        saved_name = save_upload_file(file_obj, CHECKIN_DIR)
        execute(
            "UPDATE checkin SET content=%s, checkin_date=%s, file_path=%s WHERE id=%s",
            (content, checkin_date, f"checkin/{saved_name}", checkin_id),
        )
    else:
        execute(
            "UPDATE checkin SET content=%s, checkin_date=%s WHERE id=%s",
            (content, checkin_date, checkin_id),
        )

    profile = get_student_profile_and_primary_teacher(int(current_user.id))
    if profile.get("teacher_id"):
        create_notification(
            "user",
            title="学员打卡已更新",
            content=f"学员 {profile.get('student_name') or current_user.username} 更新了 {checkin_date} 的打卡内容。",
            category="checkin",
            level="info",
            target_user_id=int(profile["teacher_id"]),
            action_path="/app/teacher/dashboard",
        )

    return api_resp(200, "更新成功", {})


@app.delete("/api/student/checkin/<int:checkin_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_checkin_delete(checkin_id):
    """学员删除自己的打卡记录。"""
    own = query_one("SELECT id, student_id FROM checkin WHERE id=%s", (checkin_id,))
    if not own or int(own["student_id"]) != int(current_user.id):
        return api_resp(403, "只能删除自己的打卡记录", {})

    checkin_row = query_one(
        "SELECT checkin_date FROM checkin WHERE id=%s",
        (checkin_id,),
    )
    execute("DELETE FROM checkin WHERE id=%s", (checkin_id,))

    profile = get_student_profile_and_primary_teacher(int(current_user.id))
    if profile.get("teacher_id"):
        create_notification(
            "user",
            title="学员打卡已删除",
            content=f"学员 {profile.get('student_name') or current_user.username} 删除了 {checkin_row.get('checkin_date') if checkin_row else ''} 的打卡记录。",
            category="checkin",
            level="warning",
            target_user_id=int(profile["teacher_id"]),
            action_path="/app/teacher/dashboard",
        )
    return api_resp(200, "删除成功", {})


@app.get("/api/supervisor/checkin_stat")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_checkin_stat():
    """
    督学查看打卡统计。
    返回每位学员的累计打卡次数与最近打卡日期。
    """
    rows = query_all(
        """
        SELECT
            u.id AS student_id,
            u.username,
            COALESCE(s.name, u.username) AS student_name,
            COUNT(c.id) AS checkin_count,
            MAX(c.checkin_date) AS last_checkin_date
        FROM users u
        LEFT JOIN student_info s ON s.user_id = u.id
        LEFT JOIN checkin c ON c.student_id = u.id
        WHERE u.role = 'student'
        GROUP BY u.id, u.username, s.name
        ORDER BY checkin_count DESC, u.id DESC
        """
    )
    total_students = len(rows)
    today_str = date.today().strftime("%Y-%m-%d")
    checked_today = query_one(
        "SELECT COUNT(DISTINCT student_id) AS total FROM checkin WHERE checkin_date = %s",
        (today_str,),
    )
    checked_count = checked_today["total"] if checked_today else 0
    unchecked_count = max(total_students - checked_count, 0)
    rate = round((checked_count / total_students) * 100, 2) if total_students else 0.0

    return api_resp(
        200,
        "查询成功",
        {
            "list": rows,
            "stat": {
                "totalStudents": total_students,
                "checkedToday": checked_count,
                "uncheckedToday": unchecked_count,
                "checkinRate": rate,
                "date": today_str,
            },
        },
    )


@app.post("/api/supervisor/checkin_remind")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_checkin_remind():
    """督学对今日未打卡学员发送提醒通知（并同步提醒对应任课老师）。"""
    payload = parse_json()
    raw_student_ids = payload.get("student_ids") if isinstance(payload, dict) else None

    selected_student_ids = []
    if isinstance(raw_student_ids, list):
        for item in raw_student_ids:
            normalized = normalize_optional_int(item, "student_id", min_value=1)
            if normalized is not None:
                selected_student_ids.append(int(normalized))
        selected_student_ids = sorted(set(selected_student_ids))

    today_str = date.today().strftime("%Y-%m-%d")

    conditions = [
        "u.role='student'",
        "NOT EXISTS (SELECT 1 FROM checkin c WHERE c.student_id=u.id AND c.checkin_date=%s)",
    ]
    params = [today_str]
    if selected_student_ids:
        placeholders = ", ".join(["%s"] * len(selected_student_ids))
        conditions.append(f"u.id IN ({placeholders})")
        params.extend(selected_student_ids)

    where_sql = " AND ".join(conditions)
    rows = query_all(
        f"""
        SELECT
            u.id AS student_id,
            u.username AS student_username,
            COALESCE(s.name, u.username) AS student_name,
            s.teacher_id,
            tu.username AS teacher_username
        FROM users u
        LEFT JOIN student_info s ON s.user_id = u.id
        LEFT JOIN users tu ON tu.id = s.teacher_id
        WHERE {where_sql}
        ORDER BY u.id DESC
        """,
        tuple(params),
    )

    if not rows:
        return api_resp(200, "今日暂无未打卡学员，无需提醒", {"student_count": 0, "teacher_count": 0})

    for item in rows:
        create_notification(
            "user",
            title="督学打卡提醒",
            content=f"请尽快完成 {today_str} 的学习打卡，保持复习节奏。",
            category="checkin",
            level="warning",
            target_user_id=int(item["student_id"]),
            action_path="/app/student/checkin",
        )

    teacher_map = {}
    for item in rows:
        teacher_id = item.get("teacher_id")
        if not teacher_id:
            continue
        teacher_id = int(teacher_id)
        teacher_map.setdefault(teacher_id, []).append(item.get("student_name") or item.get("student_username") or "学员")

    for teacher_id, names in teacher_map.items():
        preview = "、".join(names[:3])
        suffix = "等" if len(names) > 3 else ""
        create_notification(
            "user",
            title="班级未打卡提醒",
            content=f"今日仍有学员未打卡：{preview}{suffix}，请关注学习进度。",
            category="checkin",
            level="info",
            target_user_id=teacher_id,
            action_path="/app/teacher/dashboard",
        )

    return api_resp(
        200,
        "提醒发送成功",
        {
            "student_count": len(rows),
            "teacher_count": len(teacher_map),
            "date": today_str,
        },
    )


@app.get("/api/supervisor/evaluation_stat")
@login_required
@role_required("supervisor")
@handle_errors("数据库操作失败")
def supervisor_evaluation_stat():
    """督学查看评价统计（按老师聚合）。"""
    rows = query_all(
        """
        SELECT
            u.id AS teacher_id,
            u.username AS teacher_username,
            COUNT(e.id) AS evaluation_count,
            ROUND(AVG(e.score), 2) AS avg_score
        FROM users u
        LEFT JOIN evaluation e ON e.teacher_id = u.id
        WHERE u.role = 'teacher'
        GROUP BY u.id, u.username
        ORDER BY avg_score DESC, evaluation_count DESC
        """
    )
    return api_resp(200, "查询成功", rows)


# ==============================
# 评价接口
# ==============================
@app.post("/api/student/evaluate_teacher")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def evaluate_teacher():
    """
    学员评价老师（每人对同一老师仅 1 次）。

    核心逻辑：
    1) 校验 teacher_id 对应用户且角色为 teacher
    2) 校验当前学生是否已经评价过该老师
    3) 未评价则插入记录
    """
    payload = parse_json()
    teacher_id = payload.get("teacher_id")
    score = payload.get("score")
    content = mask_forbidden_text((payload.get("content") or "").strip())

    validate_required(payload, ["teacher_id", "score"])
    teacher_id = normalize_optional_int(teacher_id, "teacher_id", min_value=1)
    score = normalize_score(score)

    teacher = query_one("SELECT id, role FROM users WHERE id = %s", (teacher_id,))
    if not teacher or teacher["role"] != "teacher":
        return api_resp(400, "teacher_id 不存在或不是任课老师", {})

    related_teacher_ids = get_student_evaluation_teacher_ids(int(current_user.id))
    if related_teacher_ids and int(teacher_id) not in set(related_teacher_ids):
        return api_resp(400, "该老师不在当前学习范围内", {})

    # 关键逻辑：同一学员对同一老师仅能评价一次
    exists = query_one(
        "SELECT id FROM evaluation WHERE student_id = %s AND teacher_id = %s",
        (int(current_user.id), teacher_id),
    )
    if exists:
        return api_resp(400, "你已经评价过该老师，不能重复评价", {})

    evaluation_id = insert_and_get_id(
        """
        INSERT INTO evaluation (student_id, teacher_id, score, content, create_time)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            int(current_user.id),
            teacher_id,
            score,
            content,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    create_notification(
        "user",
        title="收到新的学员评价",
        content=f"学员 {current_user.username} 对你的课程提交了评价，请及时查看反馈。",
        category="evaluation",
        level="info",
        target_user_id=int(teacher_id),
        action_path="/app/teacher/evaluation-list",
    )
    create_notification(
        "role",
        title="评价动态提醒",
        content=f"学员 {current_user.username} 提交了任课老师评价。",
        category="evaluation",
        level="info",
        target_role="supervisor",
        action_path="/app/supervisor/dashboard",
    )

    return api_resp(200, "评价成功", {"evaluation_id": evaluation_id})


@app.get("/api/student/evaluation_list")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_evaluation_list():
    """学员查看自己的评价列表。"""
    rows = query_all(
        """
        SELECT e.id, e.student_id, e.teacher_id, t.username AS teacher_username,
               e.score, e.content, e.create_time
        FROM evaluation e
        LEFT JOIN users t ON t.id = e.teacher_id
        WHERE e.student_id = %s
        ORDER BY e.id DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


@app.put("/api/student/evaluation/<int:evaluation_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_evaluation_update(evaluation_id):
    """学员编辑自己的评价。"""
    payload = parse_json()
    score = payload.get("score")
    content = mask_forbidden_text((payload.get("content") or "").strip())
    score = normalize_score(score)

    own = query_one(
        "SELECT id, teacher_id FROM evaluation WHERE id=%s AND student_id=%s",
        (evaluation_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能编辑自己的评价", {})

    execute("UPDATE evaluation SET score=%s, content=%s WHERE id=%s", (score, content, evaluation_id))
    if own.get("teacher_id"):
        create_notification(
            "user",
            title="学员评价已更新",
            content=f"学员 {current_user.username} 更新了对你课程的评价。",
            category="evaluation",
            level="info",
            target_user_id=int(own["teacher_id"]),
            action_path="/app/teacher/evaluation-list",
        )
    return api_resp(200, "更新成功", {})


@app.delete("/api/student/evaluation/<int:evaluation_id>")
@login_required
@role_required("student")
@handle_errors("数据库操作失败")
def student_evaluation_delete(evaluation_id):
    """学员删除自己的评价。"""
    own = query_one(
        "SELECT id, teacher_id FROM evaluation WHERE id=%s AND student_id=%s",
        (evaluation_id, int(current_user.id)),
    )
    if not own:
        return api_resp(403, "只能删除自己的评价", {})

    execute("DELETE FROM evaluation WHERE id=%s", (evaluation_id,))
    if own.get("teacher_id"):
        create_notification(
            "user",
            title="学员评价已删除",
            content=f"学员 {current_user.username} 删除了对你课程的一条评价。",
            category="evaluation",
            level="warning",
            target_user_id=int(own["teacher_id"]),
            action_path="/app/teacher/evaluation-list",
        )
    return api_resp(200, "删除成功", {})


@app.get("/api/teacher/evaluation_list")
@login_required
@role_required("teacher")
@handle_errors("数据库操作失败")
def teacher_evaluation_list():
    """任课老师查看自己的评价列表。"""
    rows = query_all(
        """
        SELECT e.id, e.student_id, su.username AS student_username,
               e.teacher_id, e.score, e.content, e.create_time
        FROM evaluation e
        LEFT JOIN users su ON e.student_id = su.id
        WHERE e.teacher_id = %s
        ORDER BY e.create_time DESC
        """,
        (int(current_user.id),),
    )
    return api_resp(200, "查询成功", rows)


# ==============================
# 管理员接口（/api/admin/*）
# ==============================
@app.post("/api/admin/login")
@handle_errors("数据库操作失败")
def admin_login():
    """管理员独立登录接口。"""
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()

    validate_required(payload, ["username", "password"])
    validate_username_password(username, password)

    row = query_one(
        "SELECT id, username, password FROM admin_users WHERE username=%s",
        (username,),
    )
    if not row or not verify_password(row["password"], password):
        return api_resp(400, "管理员账号或密码错误", {})

    session["admin_id"] = int(row["id"])
    session["admin_username"] = row["username"]

    return api_resp(
        200,
        "管理员登录成功",
        {"id": int(row["id"]), "username": row["username"]},
    )


@app.post("/api/admin/logout")
@admin_required
def admin_logout():
    """管理员退出登录。"""
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    return api_resp(200, "退出成功", {})


@app.get("/api/admin/stats")
@admin_required
@handle_errors("数据库操作失败")
def admin_stats():
    """管理员数据总览。"""
    admin_user_total = query_one("SELECT COUNT(*) AS total FROM admin_users")
    user_total = query_one("SELECT COUNT(*) AS total FROM users")
    student_total = query_one("SELECT COUNT(*) AS total FROM student_info")
    checkin_total = query_one("SELECT COUNT(*) AS total FROM checkin")
    homework_total = query_one("SELECT COUNT(*) AS total FROM homework")
    materials_total = query_one("SELECT COUNT(*) AS total FROM materials")
    evaluation_total = query_one("SELECT COUNT(*) AS total FROM evaluation")

    return api_resp(
        200,
        "查询成功",
        {
            "adminUserTotal": admin_user_total["total"] if admin_user_total else 0,
            "userTotal": user_total["total"] if user_total else 0,
            "studentTotal": student_total["total"] if student_total else 0,
            "checkinTotal": checkin_total["total"] if checkin_total else 0,
            "homeworkTotal": homework_total["total"] if homework_total else 0,
            "materialsTotal": materials_total["total"] if materials_total else 0,
            "evaluationTotal": evaluation_total["total"] if evaluation_total else 0,
        },
    )


@app.get("/api/admin/users")
@admin_required
@handle_errors("数据库操作失败")
def admin_user_list():
    """管理员查看普通用户列表（student/teacher/supervisor）。"""
    username = (request.args.get("username") or "").strip()
    role = (request.args.get("role") or "").strip()

    conditions = ["role IN ('student', 'teacher', 'supervisor')"]
    params = []

    if username:
        conditions.append("username LIKE %s")
        params.append(f"%{username}%")

    if role:
        conditions.append("role = %s")
        params.append(role)

    sql = f"""
        SELECT id, username, role, create_time
        FROM users
        WHERE {' AND '.join(conditions)}
        ORDER BY id DESC
    """
    rows = query_all(sql, params)
    return api_resp(200, "查询成功", rows)


@app.post("/api/admin/users")
@admin_required
@handle_errors("数据库操作失败")
def admin_user_create():
    """管理员创建普通用户账号。"""
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "").strip()

    validate_required(payload, ["username", "password", "role"])
    validate_role(role)
    validate_username_password(username, password)

    exists = query_one("SELECT id FROM users WHERE username=%s", (username,))
    if exists:
        return api_resp(400, "用户名已存在", {})

    user_id = insert_and_get_id(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, hash_password(password), role),
    )

    if role == "student":
        name = (payload.get("name") or username).strip()
        gender = normalize_gender(payload.get("gender"))
        age = normalize_optional_int(payload.get("age"), "age", min_value=10, max_value=80)
        major = (payload.get("major") or "").strip() or None
        grade = (payload.get("grade") or "").strip() or None
        class_name = (payload.get("class") or "").strip() or None
        teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)

        if teacher_id is not None:
            teacher = query_one("SELECT id, role FROM users WHERE id=%s", (teacher_id,))
            if not teacher or teacher["role"] != "teacher":
                raise ValidationError("teacher_id 不存在或不是任课老师")

        insert_and_get_id(
            """
            INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, name, gender, age, major, grade, class_name, teacher_id),
        )

    return api_resp(200, "创建成功", {"id": user_id})


@app.put("/api/admin/users/<int:user_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_user_update(user_id):
    """管理员更新普通用户账号信息。"""
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    role = (payload.get("role") or "").strip()
    password = (payload.get("password") or "").strip()

    old_user = query_one("SELECT id FROM users WHERE id=%s", (user_id,))
    if not old_user:
        return api_resp(400, "用户不存在", {})

    validate_required(payload, ["username", "role"])
    validate_role(role)
    if len(username) < 2 or len(username) > 32:
        raise ValidationError("username 长度需在 2-32 字符")
    if password:
        validate_username_password(username, password)

    conflict = query_one("SELECT id FROM users WHERE username=%s AND id<>%s", (username, user_id))
    if conflict:
        return api_resp(400, "用户名已被占用", {})

    if password:
        execute(
            "UPDATE users SET username=%s, role=%s, password=%s WHERE id=%s",
            (username, role, hash_password(password), user_id),
        )
    else:
        execute(
            "UPDATE users SET username=%s, role=%s WHERE id=%s",
            (username, role, user_id),
        )

    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/users/<int:user_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_user_delete(user_id):
    """管理员删除普通用户账号。"""
    if query_one("SELECT id FROM users WHERE id=%s", (user_id,)) is None:
        return api_resp(400, "用户不存在", {})

    execute("DELETE FROM users WHERE id=%s", (user_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/admin/admin_users")
@admin_required
@handle_errors("数据库操作失败")
def admin_admin_users_list():
    username = (request.args.get("username") or "").strip()
    sql = "SELECT id, username, create_time FROM admin_users"
    params = []
    if username:
        sql += " WHERE username LIKE %s"
        params.append(f"%{username}%")
    sql += " ORDER BY id DESC"
    rows = query_all(sql, params)
    return api_resp(200, "查询成功", rows)


@app.post("/api/admin/admin_users")
@admin_required
@handle_errors("数据库操作失败")
def admin_admin_users_create():
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    validate_required(payload, ["username", "password"])
    validate_username_password(username, password)

    exists = query_one("SELECT id FROM admin_users WHERE username=%s", (username,))
    if exists:
        return api_resp(400, "管理员账号已存在", {})

    admin_id = insert_and_get_id(
        "INSERT INTO admin_users (username, password) VALUES (%s, %s)",
        (username, hash_password(password)),
    )
    return api_resp(200, "创建成功", {"id": admin_id})


@app.put("/api/admin/admin_users/<int:admin_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_admin_users_update(admin_id):
    payload = parse_json()
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    validate_required(payload, ["username"])

    current = query_one("SELECT id FROM admin_users WHERE id=%s", (admin_id,))
    if not current:
        return api_resp(400, "管理员不存在", {})

    conflict = query_one("SELECT id FROM admin_users WHERE username=%s AND id<>%s", (username, admin_id))
    if conflict:
        return api_resp(400, "管理员账号已被占用", {})

    if password:
        validate_username_password(username, password)
        execute(
            "UPDATE admin_users SET username=%s, password=%s WHERE id=%s",
            (username, hash_password(password), admin_id),
        )
    else:
        execute("UPDATE admin_users SET username=%s WHERE id=%s", (username, admin_id))

    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/admin_users/<int:admin_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_admin_users_delete(admin_id):
    current = query_one("SELECT id FROM admin_users WHERE id=%s", (admin_id,))
    if not current:
        return api_resp(400, "管理员不存在", {})
    if session.get("admin_id") and int(session.get("admin_id")) == admin_id:
        return api_resp(400, "不能删除当前登录的管理员", {})
    execute("DELETE FROM admin_users WHERE id=%s", (admin_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/admin/student_info/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_student_info_list():
    rows = query_all(
        """
        SELECT id, user_id, name, gender, age, major, grade, `class` AS class_name, teacher_id
        FROM student_info ORDER BY id DESC
        """
    )

    for row in rows:
        user_id = int(row.get("user_id") or 0)
        primary_teacher_id = row.get("teacher_id")
        primary_teacher_name = None
        if primary_teacher_id:
            teacher_row = query_one(
                "SELECT username FROM users WHERE id=%s AND role='teacher' LIMIT 1",
                (int(primary_teacher_id),),
            )
            primary_teacher_name = (teacher_row or {}).get("username")

        row["primary_teacher_name"] = primary_teacher_name

        teacher_ids = get_student_related_teacher_ids(user_id) if user_id else []
        row["teacher_ids"] = teacher_ids
        row["teacher_count"] = len(teacher_ids)

        if teacher_ids:
            placeholders = ", ".join(["%s"] * len(teacher_ids))
            teacher_rows = query_all(
                f"SELECT id, username FROM users WHERE role='teacher' AND id IN ({placeholders}) ORDER BY id ASC",
                tuple(teacher_ids),
            )
            row["teacher_names"] = [item.get("username") for item in teacher_rows if item.get("username")]
        else:
            row["teacher_names"] = []

    return api_resp(200, "查询成功", rows)


@app.post("/api/admin/student_info")
@admin_required
@handle_errors("数据库操作失败")
def admin_student_info_create():
    payload = parse_json()
    user_id = normalize_optional_int(payload.get("user_id"), "user_id", min_value=1)
    name = (payload.get("name") or "").strip()
    gender = normalize_gender(payload.get("gender"))
    age = normalize_optional_int(payload.get("age"), "age", min_value=10, max_value=80)
    major = (payload.get("major") or "").strip() or None
    grade = (payload.get("grade") or "").strip() or None
    class_name = (payload.get("class_name") or payload.get("class") or "").strip() or None
    teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)

    validate_required(payload, ["user_id", "name"])

    user = query_one("SELECT id, role FROM users WHERE id=%s", (user_id,))
    if not user or user["role"] != "student":
        return api_resp(400, "user_id 不存在或不是学员", {})

    if teacher_id is not None:
        teacher = query_one("SELECT id, role FROM users WHERE id=%s", (teacher_id,))
        if not teacher or teacher["role"] != "teacher":
            return api_resp(400, "teacher_id 不存在或不是任课老师", {})

    exists = query_one("SELECT id FROM student_info WHERE user_id=%s", (user_id,))
    if exists:
        return api_resp(400, "该学员档案已存在", {})

    info_id = insert_and_get_id(
        """
        INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, name, gender, age, major, grade, class_name, teacher_id),
    )
    return api_resp(200, "创建成功", {"id": info_id})


@app.put("/api/admin/student_info/<int:info_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_student_info_update(info_id):
    payload = parse_json()
    user_id = normalize_optional_int(payload.get("user_id"), "user_id", min_value=1)
    name = (payload.get("name") or "").strip()
    gender = normalize_gender(payload.get("gender"))
    age = normalize_optional_int(payload.get("age"), "age", min_value=10, max_value=80)
    major = (payload.get("major") or "").strip() or None
    grade = (payload.get("grade") or "").strip() or None
    class_name = (payload.get("class_name") or payload.get("class") or "").strip() or None
    teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)

    validate_required(payload, ["user_id", "name"])

    existing = query_one("SELECT id FROM student_info WHERE id=%s", (info_id,))
    if not existing:
        return api_resp(400, "档案不存在", {})

    user = query_one("SELECT id, role FROM users WHERE id=%s", (user_id,))
    if not user or user["role"] != "student":
        return api_resp(400, "user_id 不存在或不是学员", {})

    if teacher_id is not None:
        teacher = query_one("SELECT id, role FROM users WHERE id=%s", (teacher_id,))
        if not teacher or teacher["role"] != "teacher":
            return api_resp(400, "teacher_id 不存在或不是任课老师", {})

    conflict = query_one("SELECT id FROM student_info WHERE user_id=%s AND id<>%s", (user_id, info_id))
    if conflict:
        return api_resp(400, "该学员已存在档案", {})

    execute(
        """
        UPDATE student_info
        SET user_id=%s, name=%s, gender=%s, age=%s, major=%s, grade=%s, `class`=%s, teacher_id=%s
        WHERE id=%s
        """,
        (user_id, name, gender, age, major, grade, class_name, teacher_id, info_id),
    )
    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/student_info/<int:info_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_student_info_delete(info_id):
    existing = query_one("SELECT id FROM student_info WHERE id=%s", (info_id,))
    if not existing:
        return api_resp(400, "档案不存在", {})
    execute("DELETE FROM student_info WHERE id=%s", (info_id,))
    return api_resp(200, "删除成功", {})


@app.post("/api/admin/homework")
@admin_required
@handle_errors("数据库操作失败")
def admin_homework_create():
    payload = parse_json()
    teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)
    title = mask_forbidden_text((payload.get("title") or "").strip())
    content = mask_forbidden_text((payload.get("content") or "").strip())
    deadline = (payload.get("deadline") or "").strip()
    validate_required(payload, ["teacher_id", "title", "deadline"])
    if not is_valid_datetime(deadline):
        return api_resp(400, "deadline 格式错误，应为 YYYY-MM-DD HH:MM:SS", {})
    teacher = query_one("SELECT id, role FROM users WHERE id=%s", (teacher_id,))
    if not teacher or teacher["role"] != "teacher":
        return api_resp(400, "teacher_id 不存在或不是任课老师", {})
    homework_id = insert_and_get_id(
        "INSERT INTO homework (teacher_id, title, content, publish_time, deadline) VALUES (%s, %s, %s, %s, %s)",
        (teacher_id, title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), deadline),
    )
    return api_resp(200, "创建成功", {"id": homework_id})


@app.put("/api/admin/homework/<int:homework_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_homework_update(homework_id):
    payload = parse_json()
    title = mask_forbidden_text((payload.get("title") or "").strip())
    content = mask_forbidden_text((payload.get("content") or "").strip())
    deadline = (payload.get("deadline") or "").strip()
    validate_required(payload, ["title", "deadline"])
    if not is_valid_datetime(deadline):
        return api_resp(400, "deadline 格式错误，应为 YYYY-MM-DD HH:MM:SS", {})
    existing = query_one("SELECT id FROM homework WHERE id=%s", (homework_id,))
    if not existing:
        return api_resp(400, "作业不存在", {})
    execute("UPDATE homework SET title=%s, content=%s, deadline=%s WHERE id=%s", (title, content, deadline, homework_id))
    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/homework/<int:homework_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_homework_delete(homework_id):
    existing = query_one("SELECT id FROM homework WHERE id=%s", (homework_id,))
    if not existing:
        return api_resp(400, "作业不存在", {})
    execute("DELETE FROM homework WHERE id=%s", (homework_id,))
    return api_resp(200, "删除成功", {})


@app.post("/api/admin/materials")
@admin_required
@handle_errors("数据库操作失败")
def admin_materials_create():
    payload = parse_json()
    teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)
    title = mask_forbidden_text((payload.get("title") or "").strip())
    file_path = (payload.get("file_path") or "").strip()
    video_url = normalize_optional_video_url(payload.get("video_url"))
    validate_required(payload, ["teacher_id", "title", "file_path"])
    teacher = query_one("SELECT id, role FROM users WHERE id=%s", (teacher_id,))
    if not teacher or teacher["role"] != "teacher":
        return api_resp(400, "teacher_id 不存在或不是任课老师", {})
    material_id = insert_and_get_id(
        "INSERT INTO materials (teacher_id, title, file_path, video_url, upload_time, download_count) VALUES (%s, %s, %s, %s, %s, %s)",
        (teacher_id, title, file_path, video_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
    )
    return api_resp(200, "创建成功", {"id": material_id})


@app.put("/api/admin/materials/<int:material_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_materials_update(material_id):
    payload = parse_json()
    title = mask_forbidden_text((payload.get("title") or "").strip())
    file_path = (payload.get("file_path") or "").strip()
    video_url = normalize_optional_video_url(payload.get("video_url"))
    validate_required(payload, ["title", "file_path"])
    existing = query_one("SELECT id FROM materials WHERE id=%s", (material_id,))
    if not existing:
        return api_resp(400, "资料不存在", {})
    execute("UPDATE materials SET title=%s, file_path=%s, video_url=%s WHERE id=%s", (title, file_path, video_url, material_id))
    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/materials/<int:material_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_materials_delete(material_id):
    existing = query_one("SELECT id FROM materials WHERE id=%s", (material_id,))
    if not existing:
        return api_resp(400, "资料不存在", {})
    execute("DELETE FROM materials WHERE id=%s", (material_id,))
    return api_resp(200, "删除成功", {})


@app.post("/api/admin/checkin")
@admin_required
@handle_errors("数据库操作失败")
def admin_checkin_create():
    payload = parse_json()
    student_id = normalize_optional_int(payload.get("student_id"), "student_id", min_value=1)
    content = mask_forbidden_text((payload.get("content") or "").strip())
    file_path = (payload.get("file_path") or "").strip() or None
    checkin_date = (payload.get("checkin_date") or "").strip()
    validate_required(payload, ["student_id", "checkin_date"])
    if not is_valid_date(checkin_date):
        return api_resp(400, "checkin_date 格式错误，应为 YYYY-MM-DD", {})
    student = query_one("SELECT id, role FROM users WHERE id=%s", (student_id,))
    if not student or student["role"] != "student":
        return api_resp(400, "student_id 不存在或不是学员", {})
    checkin_id = insert_and_get_id(
        "INSERT INTO checkin (student_id, content, file_path, checkin_date, create_time) VALUES (%s, %s, %s, %s, %s)",
        (student_id, content, file_path, checkin_date, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    return api_resp(200, "创建成功", {"id": checkin_id})


@app.put("/api/admin/checkin/<int:checkin_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_checkin_update(checkin_id):
    payload = parse_json()
    content = mask_forbidden_text((payload.get("content") or "").strip())
    file_path = (payload.get("file_path") or "").strip() or None
    checkin_date = (payload.get("checkin_date") or "").strip()
    validate_required(payload, ["checkin_date"])
    if not is_valid_date(checkin_date):
        return api_resp(400, "checkin_date 格式错误，应为 YYYY-MM-DD", {})
    existing = query_one("SELECT id FROM checkin WHERE id=%s", (checkin_id,))
    if not existing:
        return api_resp(400, "打卡不存在", {})
    execute("UPDATE checkin SET content=%s, file_path=%s, checkin_date=%s WHERE id=%s", (content, file_path, checkin_date, checkin_id))
    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/checkin/<int:checkin_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_checkin_delete(checkin_id):
    existing = query_one("SELECT id FROM checkin WHERE id=%s", (checkin_id,))
    if not existing:
        return api_resp(400, "打卡不存在", {})
    execute("DELETE FROM checkin WHERE id=%s", (checkin_id,))
    return api_resp(200, "删除成功", {})


@app.post("/api/admin/evaluation")
@admin_required
@handle_errors("数据库操作失败")
def admin_evaluation_create():
    payload = parse_json()
    student_id = normalize_optional_int(payload.get("student_id"), "student_id", min_value=1)
    teacher_id = normalize_optional_int(payload.get("teacher_id"), "teacher_id", min_value=1)
    score = normalize_score(payload.get("score"))
    content = mask_forbidden_text((payload.get("content") or "").strip())
    validate_required(payload, ["student_id", "teacher_id", "score"])
    evaluation_id = insert_and_get_id(
        "INSERT INTO evaluation (student_id, teacher_id, score, content, create_time) VALUES (%s, %s, %s, %s, %s)",
        (student_id, teacher_id, score, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    return api_resp(200, "创建成功", {"id": evaluation_id})


@app.put("/api/admin/evaluation/<int:evaluation_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_evaluation_update(evaluation_id):
    payload = parse_json()
    score = normalize_score(payload.get("score"))
    content = mask_forbidden_text((payload.get("content") or "").strip())
    existing = query_one("SELECT id FROM evaluation WHERE id=%s", (evaluation_id,))
    if not existing:
        return api_resp(400, "评价不存在", {})
    execute("UPDATE evaluation SET score=%s, content=%s WHERE id=%s", (score, content, evaluation_id))
    return api_resp(200, "更新成功", {})


@app.delete("/api/admin/evaluation/<int:evaluation_id>")
@admin_required
@handle_errors("数据库操作失败")
def admin_evaluation_delete(evaluation_id):
    existing = query_one("SELECT id FROM evaluation WHERE id=%s", (evaluation_id,))
    if not existing:
        return api_resp(400, "评价不存在", {})
    execute("DELETE FROM evaluation WHERE id=%s", (evaluation_id,))
    return api_resp(200, "删除成功", {})


@app.get("/api/admin/checkin/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_checkin_list():
    rows = query_all(
        """
        SELECT
            c.id,
            c.student_id,
            COALESCE(NULLIF(si.name, ''), su.username) AS student_name,
            c.content,
            c.file_path,
            c.checkin_date,
            c.create_time
        FROM checkin c
        LEFT JOIN student_info si ON si.user_id = c.student_id
        LEFT JOIN users su ON su.id = c.student_id
        ORDER BY c.id DESC
        """
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/admin/homework/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_homework_list():
    rows = query_all(
        """
        SELECT
            h.id,
            h.teacher_id,
            COALESCE(tu.username, CONCAT('老师', h.teacher_id)) AS teacher_name,
            h.title,
            h.content,
            h.publish_time,
            h.deadline
        FROM homework h
        LEFT JOIN users tu ON tu.id = h.teacher_id
        ORDER BY h.id DESC
        """
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/admin/materials/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_materials_list():
    rows = query_all(
        """
        SELECT
            m.id,
            m.teacher_id,
            COALESCE(tu.username, CONCAT('老师', m.teacher_id)) AS teacher_name,
            m.title,
            m.file_path,
            m.video_url,
            m.download_count,
            m.upload_time
        FROM materials m
        LEFT JOIN users tu ON tu.id = m.teacher_id
        ORDER BY m.id DESC
        """
    )
    return api_resp(200, "查询成功", rows)


@app.get("/api/admin/evaluation/list")
@admin_required
@handle_errors("数据库操作失败")
def admin_evaluation_list():
    rows = query_all(
        """
        SELECT
            e.id,
            e.student_id,
            COALESCE(NULLIF(si.name, ''), su.username) AS student_name,
            e.teacher_id,
            COALESCE(tu.username, CONCAT('老师', e.teacher_id)) AS teacher_name,
            e.score,
            e.content,
            e.create_time
        FROM evaluation e
        LEFT JOIN student_info si ON si.user_id = e.student_id
        LEFT JOIN users su ON su.id = e.student_id
        LEFT JOIN users tu ON tu.id = e.teacher_id
        ORDER BY e.id DESC
        """
    )
    return api_resp(200, "查询成功", rows)


def _admin_batch_delete(table_name, id_list):
    """管理员批量删除通用逻辑。"""
    if not id_list or not isinstance(id_list, list):
        return api_resp(400, "ids 不能为空", {})

    clean_ids = []
    for item in id_list:
        if isinstance(item, bool):
            continue
        if str(item).isdigit():
            clean_ids.append(int(item))
    if not clean_ids:
        return api_resp(400, "ids 参数无效", {})

    placeholders = ",".join(["%s"] * len(clean_ids))
    sql = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"
    affected = execute(sql, tuple(clean_ids))
    return api_resp(200, "批量删除成功", {"affected": affected})


@app.post("/api/admin/checkin/delete_batch")
@admin_required
@handle_errors("数据库操作失败")
def admin_checkin_delete_batch():
    payload = parse_json()
    return _admin_batch_delete("checkin", payload.get("ids"))


@app.post("/api/admin/homework/delete_batch")
@admin_required
@handle_errors("数据库操作失败")
def admin_homework_delete_batch():
    payload = parse_json()
    return _admin_batch_delete("homework", payload.get("ids"))


@app.post("/api/admin/materials/delete_batch")
@admin_required
@handle_errors("数据库操作失败")
def admin_materials_delete_batch():
    payload = parse_json()
    return _admin_batch_delete("materials", payload.get("ids"))


@app.post("/api/admin/evaluation/delete_batch")
@admin_required
@handle_errors("数据库操作失败")
def admin_evaluation_delete_batch():
    payload = parse_json()
    return _admin_batch_delete("evaluation", payload.get("ids"))


@app.get("/api/admin/checkin/export")
@admin_required
@handle_errors("导出失败")
def admin_checkin_export():
    rows = query_all("SELECT id, student_id, content, file_path, checkin_date, create_time FROM checkin ORDER BY id DESC")
    return build_csv_response("admin_checkin.csv", rows, ["id", "student_id", "content", "file_path", "checkin_date", "create_time"])


@app.get("/api/admin/homework/export")
@admin_required
@handle_errors("导出失败")
def admin_homework_export():
    rows = query_all("SELECT id, teacher_id, title, content, publish_time, deadline FROM homework ORDER BY id DESC")
    return build_csv_response("admin_homework.csv", rows, ["id", "teacher_id", "title", "content", "publish_time", "deadline"])


@app.get("/api/admin/materials/export")
@admin_required
@handle_errors("导出失败")
def admin_materials_export():
    rows = query_all(
        "SELECT id, teacher_id, title, file_path, video_url, download_count, upload_time FROM materials ORDER BY id DESC"
    )
    return build_csv_response(
        "admin_materials.csv",
        rows,
        ["id", "teacher_id", "title", "file_path", "video_url", "download_count", "upload_time"],
    )


@app.get("/api/admin/evaluation/export")
@admin_required
@handle_errors("导出失败")
def admin_evaluation_export():
    rows = query_all("SELECT id, student_id, teacher_id, score, content, create_time FROM evaluation ORDER BY id DESC")
    return build_csv_response("admin_evaluation.csv", rows, ["id", "student_id", "teacher_id", "score", "content", "create_time"])


# ==============================
# 文件访问与健康检查
# ==============================
@app.get("/uploads/<path:filename>")
def serve_upload_file(filename):
    """提供上传文件访问（资料/打卡截图）。"""
    response = send_from_directory(app.config["UPLOAD_DIR"], filename)

    # 文本资料统一声明 UTF-8，避免浏览器按本地编码猜测导致乱码
    lower_name = (filename or "").lower()
    if lower_name.endswith((".txt", ".md", ".csv", ".json", ".xml")):
        response.headers["Content-Type"] = "text/plain; charset=utf-8"

    return response


@app.get("/api/health")
def health():
    """后端健康检查接口。"""
    return api_resp(200, "ok", {"service": "hongshi-backend", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


if __name__ == "__main__":
    # 开发环境启动方式
    app.run(host="0.0.0.0", port=5000, debug=True)
