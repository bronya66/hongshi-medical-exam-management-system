import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, insert_and_get_id, query_all, query_one


PASSWORD_HASH = generate_password_hash("123456")
ADMIN_HASH = generate_password_hash("admin123")

STUDENT_NAMES = ["张晨", "李悦", "王涵", "陈诺", "赵宁", "孙博", "周妍", "吴凯"]
TEACHER_NAMES = ["李明", "周凯", "陈洁", "王雪"]
SUPERVISOR_NAMES = ["孙华", "刘颖"]


def ensure_admin_default():
    exists = query_one("SELECT id FROM admin_users WHERE username=%s", ("admin",))
    if exists:
        execute("UPDATE admin_users SET password=%s WHERE username=%s", (ADMIN_HASH, "admin"))
    else:
        insert_and_get_id(
            "INSERT INTO admin_users (username, password) VALUES (%s, %s)",
            ("admin", ADMIN_HASH),
        )


def cleanup_old_seed_data():
    name_list = STUDENT_NAMES + TEACHER_NAMES + SUPERVISOR_NAMES
    name_filter = " OR ".join([f"username='{name}'" for name in name_list])
    user_filter = (
        "username LIKE 'test_%%' "
        "OR username LIKE 'student_med%%' "
        "OR username LIKE 'stu_%%' "
        "OR username LIKE 'teacher_clinical%%' "
        "OR username LIKE 'teacher_basic%%' "
        "OR username LIKE 'teacher_oral%%' "
        "OR username LIKE 'supervisor_manage%%' "
        "OR username LIKE 'student_eval_%%' "
        "OR username LIKE 'student_feedback_%%' "
        "OR username LIKE 'student_tmp_%%'"
    )
    if name_filter:
        user_filter = f"({user_filter}) OR ({name_filter})"
    execute(f"DELETE FROM homework_submission WHERE student_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM evaluation WHERE student_id IN (SELECT id FROM users WHERE {user_filter}) OR teacher_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM checkin WHERE student_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM materials WHERE teacher_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM homework WHERE teacher_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM student_info WHERE user_id IN (SELECT id FROM users WHERE {user_filter})")
    execute(f"DELETE FROM users WHERE {user_filter}")


def create_user(username, role):
    return insert_and_get_id(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, PASSWORD_HASH, role),
    )


def seed_users():
    teacher_usernames = TEACHER_NAMES
    supervisor_usernames = SUPERVISOR_NAMES
    student_usernames = STUDENT_NAMES

    teacher_ids = [create_user(username, "teacher") for username in teacher_usernames]
    supervisor_ids = [create_user(username, "supervisor") for username in supervisor_usernames]
    student_ids = [create_user(username, "student") for username in student_usernames]
    return teacher_ids, supervisor_ids, student_ids


def seed_student_info(student_ids, teacher_ids):
    genders = ["male", "female", "male", "female", "male", "male", "female", "male"]
    majors = ["临床医学", "基础医学", "口腔医学", "护理学", "药学", "影像医学", "预防医学", "麻醉学"]
    grades = ["2023", "2024", "2025", "2023", "2024", "2025", "2024", "2025"]
    classes = ["A班", "B班", "C班", "A班", "B班", "C班", "A班", "B班"]

    for index, student_id in enumerate(student_ids):
        teacher_id = teacher_ids[index % len(teacher_ids)]
        age = 22 + (index % 4)
        insert_and_get_id(
            """
            INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (student_id, STUDENT_NAMES[index], genders[index], age, majors[index], grades[index], classes[index], teacher_id),
        )


def seed_homework(teacher_ids):
    subjects = ["生理学", "病理学", "药理学", "内科学", "外科学"]
    created = 0
    for teacher_index, teacher_id in enumerate(teacher_ids, start=1):
        for homework_index in range(1, 5):
            subject = subjects[(teacher_index + homework_index) % len(subjects)]
            question_count = 15 + ((teacher_index * 3 + homework_index * 5) % 16)
            deadline = datetime.now() + timedelta(days=homework_index * 3)
            insert_and_get_id(
                """
                INSERT INTO homework (teacher_id, title, content, publish_time, deadline)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    teacher_id,
                    f"{subject}作业{homework_index}",
                    f"请完成{subject}章节复习与{question_count}道专项练习题，并提交错题总结（老师{teacher_index}）",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    deadline.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created += 1
    return created


def seed_materials(teacher_ids):
    tags = ["课件", "习题", "参考资料", "重点总结", "模拟卷"]
    created = 0
    for teacher_index, teacher_id in enumerate(teacher_ids, start=1):
        for material_index in range(1, 5):
            tag = tags[(teacher_index + material_index) % len(tags)]
            insert_and_get_id(
                """
                INSERT INTO materials (teacher_id, title, file_path, upload_time, download_count)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    teacher_id,
                    f"{tag}-老师{teacher_index}-第{material_index}版",
                    f"materials/teacher_{teacher_index}_{material_index}.pdf",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    random.randint(5, 60),
                ),
            )
            created += 1
    return created


def seed_checkin(student_ids):
    created = 0
    for student_index, student_id in enumerate(student_ids, start=1):
        for offset in range(1, 7):
            checkin_date = (datetime.now() - timedelta(days=offset)).strftime("%Y-%m-%d")
            screenshot = f"checkin/student_{student_index}_{offset}.png" if offset % 2 == 0 else None
            insert_and_get_id(
                """
                INSERT INTO checkin (student_id, content, file_path, checkin_date, create_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    student_id,
                    f"第{offset}天学习打卡：完成英语阅读、专业课笔记整理和错题复盘。",
                    screenshot,
                    checkin_date,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created += 1
    return created


def seed_evaluation(student_ids, teacher_ids):
    comments = [
        "讲解清晰，重点突出，建议增加课堂互动。",
        "作业反馈及时，答疑认真，学习收获明显。",
        "课程体系完整，案例丰富，复习效率提升很大。",
        "授课节奏合理，建议补充更多临床应用题。",
        "资料整理很系统，对冲刺复习帮助很大。",
    ]
    created = 0
    for student_index, student_id in enumerate(student_ids):
        for teacher_index, teacher_id in enumerate(teacher_ids):
            score = [5, 4, 5, 3, 4][(student_index + teacher_index) % 5]
            comment = comments[(student_index + teacher_index) % len(comments)]
            insert_and_get_id(
                """
                INSERT INTO evaluation (student_id, teacher_id, score, content, create_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    student_id,
                    teacher_id,
                    score,
                    comment,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created += 1
    return created


def seed_homework_submission(student_ids):
    homework_rows = query_all("SELECT id, title, content FROM homework ORDER BY id ASC")
    if not homework_rows:
        return 0

    attachment_dir = BACKEND_DIR / "uploads" / "homework"
    attachment_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for student_index, student_id in enumerate(student_ids):
        for offset in range(2):
            homework_row = homework_rows[(student_index + offset) % len(homework_rows)]
            homework_id = homework_row["id"]
            submit_time = datetime.now() - timedelta(days=offset)
            plan_mode = ["限时训练", "错因复盘", "模板套写"][ (student_index + offset) % 3 ]
            weak_point = ["知识点边界", "审题速度", "主观题表达", "关键词覆盖"][ (student_id + offset) % 4 ]
            requirement = (str(homework_row.get("content") or "").split("\n")[0] or "完成作业任务").strip()
            filename = f"submission_seed_stu{student_id}_hw{homework_id}_r{offset + 1}.txt"
            target_path = attachment_dir / filename
            target_path.write_text(
                (
                    f"学员ID：{student_id}\n"
                    f"作业ID：{homework_id}\n"
                    f"作业标题：{homework_row.get('title') or ''}\n"
                    f"提交轮次：第{offset + 1}次\n\n"
                    f"作业要求：{homework_row.get('content') or ''}\n\n"
                    "本次训练完成情况：\n"
                    f"1. 按“{requirement}”完成基础任务。\n"
                    f"2. 采用{plan_mode}策略完成本轮训练。\n"
                    f"3. 重点修正{weak_point}并输出改进计划。\n"
                ),
                encoding="utf-8",
            )
            insert_and_get_id(
                """
                INSERT INTO homework_submission (homework_id, student_id, content, file_path, score, feedback, submit_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    homework_id,
                    student_id,
                    f"围绕《{homework_row.get('title') or '阶段作业'}》完成第{offset + 1}次训练，按{plan_mode}推进并修正{weak_point}。",
                    f"homework/{filename}",
                    random.randint(70, 95),
                    "完成较好，继续保持。",
                    submit_time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created += 1
    return created


def get_summary():
    return {
        "users": query_one("SELECT COUNT(*) AS total FROM users")['total'],
        "student_info": query_one("SELECT COUNT(*) AS total FROM student_info")['total'],
        "homework": query_one("SELECT COUNT(*) AS total FROM homework")['total'],
        "materials": query_one("SELECT COUNT(*) AS total FROM materials")['total'],
        "checkin": query_one("SELECT COUNT(*) AS total FROM checkin")['total'],
        "evaluation": query_one("SELECT COUNT(*) AS total FROM evaluation")['total'],
        "homework_submission": query_one("SELECT COUNT(*) AS total FROM homework_submission")['total'],
        "admin_users": query_one("SELECT COUNT(*) AS total FROM admin_users")['total'],
    }


def main():
    random.seed(42)
    ensure_admin_default()
    cleanup_old_seed_data()
    teacher_ids, supervisor_ids, student_ids = seed_users()
    seed_student_info(student_ids, teacher_ids)
    homework_count = seed_homework(teacher_ids)
    materials_count = seed_materials(teacher_ids)
    checkin_count = seed_checkin(student_ids)
    evaluation_count = seed_evaluation(student_ids, teacher_ids)
    submission_count = seed_homework_submission(student_ids)

    print("示例业务数据生成完成")
    print({
        "teachers": len(teacher_ids),
        "supervisors": len(supervisor_ids),
        "students": len(student_ids),
        "homework_created": homework_count,
        "materials_created": materials_count,
        "checkin_created": checkin_count,
        "evaluation_created": evaluation_count,
        "homework_submission_created": submission_count,
        "summary": get_summary(),
    })


if __name__ == "__main__":
    main()
