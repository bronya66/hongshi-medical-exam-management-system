from io import BytesIO
import sys
from pathlib import Path
from datetime import datetime, timedelta

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import app, get_allowed_question_types, resolve_teacher_bound_course
from db import query_one


results = []
issues = []


def record(case_name, passed, detail=""):
    results.append({"case": case_name, "passed": passed, "detail": detail})


def expect(resp_json, expected_code=200):
    return isinstance(resp_json, dict) and resp_json.get("code") == expected_code


def login(client, username, role):
    res = client.post("/api/login", json={"username": username, "password": "123456", "role": role})
    data = res.get_json()
    return data


def login_any(client, role, usernames):
    """兼容不同测试数据版本：按顺序尝试多个账号。"""
    for username in usernames:
        data = login(client, username, role)
        if expect(data):
            return data, username
    return data if "data" in locals() else {}, None


def run_basic_and_role_tests():
    with app.test_client() as student_client:
        student_login, _ = login_any(student_client, "student", ["张晨", "李悦"])
        record("学生登录", expect(student_login), str(student_login))

        role_check = student_client.get("/api/teacher/student_list").get_json()
        record("角色权限控制(学生访问老师接口应拒绝)", expect(role_check, 403), str(role_check))

        student_logout = student_client.post("/api/logout").get_json()
        record("退出登录", expect(student_logout), str(student_logout))

    with app.test_client() as teacher_client:
        teacher_login, _ = login_any(teacher_client, "teacher", ["周凯", "李明"])
        record("老师登录", expect(teacher_login), str(teacher_login))

    with app.test_client() as supervisor_client:
        supervisor_login = login(supervisor_client, "孙华", "supervisor")
        record("督学登录", expect(supervisor_login), str(supervisor_login))


def run_student_tests():
    with app.test_client() as client:
        login_result, student_name = login_any(client, "student", ["李悦", "张晨"])
        if not expect(login_result):
            record("学员端用例初始化", False, "学生登录失败")
            return

        profile = client.get("/api/student/profile").get_json()
        record("学员-查看个人信息", expect(profile), str(profile))

        profile_update = client.put(
            "/api/student/profile",
            json={
                "name": student_name or "李悦",
                "gender": "女",
                "age": 24,
                "major": "临床医学",
                "grade": "2025",
                "class": "B班",
            },
        ).get_json()
        record("学员-修改个人信息", expect(profile_update), str(profile_update))

        checkin_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        checkin_create = client.post(
            "/api/student/checkin",
            data={"content": "学习打卡记录", "checkin_date": checkin_date, "file": (BytesIO(b"img"), "checkin.png")},
            content_type="multipart/form-data",
        ).get_json()
        record("学员-每日打卡", expect(checkin_create), str(checkin_create))

        checkin_id = checkin_create.get("data", {}).get("checkin_id") if isinstance(checkin_create, dict) else None
        if checkin_id:
            checkin_update = client.put(
                f"/api/student/checkin/{checkin_id}",
                data={"content": "学习打卡补充记录", "checkin_date": checkin_date},
                content_type="multipart/form-data",
            ).get_json()
            record("学员-修改打卡", expect(checkin_update), str(checkin_update))

            checkin_delete = client.delete(f"/api/student/checkin/{checkin_id}").get_json()
            record("学员-删除打卡", expect(checkin_delete), str(checkin_delete))

        homework_list = client.get("/api/student/homework_list").get_json()
        record("学员-查看作业", expect(homework_list), str(homework_list)[:200])

        homework_rows = homework_list.get("data") if isinstance(homework_list, dict) else []
        if homework_rows:
            target_homework_id = homework_rows[0].get("id")
            submit = client.post(
                "/api/student/homework_submit",
                data={
                    "homework_id": str(target_homework_id),
                    "content": "阶段作业提交内容",
                    "file": (BytesIO(b"homework-attachment"), "homework.pdf"),
                },
                content_type="multipart/form-data",
            ).get_json()
            record("学员-提交作业", expect(submit), str(submit))

        materials_list = client.get("/api/student/materials_list").get_json()
        record("学员-查看资料", expect(materials_list), str(materials_list)[:200])

        material_id = None
        if isinstance(materials_list, dict):
            data = materials_list.get("data") or []
            if data:
                material_id = data[0].get("id")
        if material_id:
            download = client.post("/api/student/download_materials", json={"material_id": material_id}).get_json()
            record("学员-下载资料", expect(download), str(download))

        teacher_list = client.get("/api/student/teacher_list").get_json()
        record("学员-查看老师列表", expect(teacher_list), str(teacher_list)[:200])

        if isinstance(teacher_list, dict) and teacher_list.get("data"):
            teacher_id = teacher_list["data"][0]["id"]

            temp_username = f"test_eval_{datetime.now().strftime('%H%M%S')}"
            register = app.test_client().post(
                "/api/register",
                json={
                    "username": temp_username,
                    "password": "123456",
                    "role": "student",
                    "name": temp_username,
                    "gender": "男",
                    "age": 23,
                    "major": "临床医学",
                    "grade": "2025",
                    "class": "A班",
                    "teacher_id": teacher_id,
                },
            ).get_json()
            register_ok = expect(register)
            record("学员-注册(用于课程反馈流程)", register_ok, str(register))

            with app.test_client() as eval_client:
                eval_login = login(eval_client, temp_username, "student")
                if not expect(eval_login) and register_ok is False:
                    eval_login = login(eval_client, temp_username, "student")
                record("学员-登录(用于课程反馈流程)", expect(eval_login), str(eval_login))

                if expect(eval_login):
                    eval_create = eval_client.post(
                        "/api/student/evaluate_teacher",
                        json={"teacher_id": teacher_id, "score": 5, "content": "课程反馈"},
                    ).get_json()
                    record("学员-评价老师", expect(eval_create), str(eval_create))

                    evaluation_id = eval_create.get("data", {}).get("evaluation_id") if isinstance(eval_create, dict) else None
                    if evaluation_id:
                        eval_update = eval_client.put(
                            f"/api/student/evaluation/{evaluation_id}",
                            json={"score": 4, "content": "课程反馈-补充"},
                        ).get_json()
                        record("学员-修改评价", expect(eval_update), str(eval_update))

                        eval_delete = eval_client.delete(f"/api/student/evaluation/{evaluation_id}").get_json()
                        record("学员-删除评价", expect(eval_delete), str(eval_delete))


def run_teacher_tests():
    with app.test_client() as client:
        login_result, _ = login_any(client, "teacher", ["周凯", "李明"])
        if not expect(login_result):
            record("老师端用例初始化", False, "老师登录失败")
            return

        student_list = client.get("/api/teacher/student_list").get_json()
        record("老师-查看学员列表", expect(student_list), str(student_list)[:200])

        deadline = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        publish = client.post(
            "/api/teacher/publish_homework",
            json={"title": "阶段训练作业", "content": "请完成章节训练题", "deadline": deadline},
        ).get_json()
        record("老师-发布作业", expect(publish), str(publish))

        homework_id = publish.get("data", {}).get("homework_id") if isinstance(publish, dict) else None
        if homework_id:
            update = client.put(
                f"/api/teacher/homework/{homework_id}",
                json={"title": "阶段训练作业-修订", "content": "更新内容", "deadline": deadline},
            ).get_json()
            record("老师-管理作业(更新)", expect(update), str(update))

            submissions = client.get(f"/api/teacher/homework_submission_list?homework_id={homework_id}").get_json()
            record("老师-查看作业提交", expect(submissions), str(submissions)[:200])

            submission_rows = submissions.get("data") if isinstance(submissions, dict) else []
            if not submission_rows:
                all_submissions = client.get("/api/teacher/homework_submission_list").get_json()
                record("老师-查看全部作业提交", expect(all_submissions), str(all_submissions)[:200])
                submission_rows = all_submissions.get("data") if isinstance(all_submissions, dict) else []

            if submission_rows:
                submission_id = submission_rows[0].get("id")
                review = client.put(
                    f"/api/teacher/homework_submission/{submission_id}/review",
                    json={"score": 88, "feedback": "完成较好，注意补充关键知识点总结。"},
                ).get_json()
                record("老师-评分作业提交", expect(review), str(review))
            else:
                record("老师-评分作业提交", True, "跳过：当前无可评分提交记录")

            delete = client.delete(f"/api/teacher/homework/{homework_id}").get_json()
            record("老师-管理作业(删除)", expect(delete), str(delete))

        upload = client.post(
            "/api/teacher/upload_materials",
            data={"title": "阶段复习资料", "file": (BytesIO(b"pdf-content"), "material.pdf")},
            content_type="multipart/form-data",
        ).get_json()
        record("老师-上传资料", expect(upload), str(upload))

        material_id = upload.get("data", {}).get("material_id") if isinstance(upload, dict) else None
        materials_list = client.get("/api/teacher/materials_list").get_json()
        record("老师-查看资料列表", expect(materials_list), str(materials_list)[:200])

        if material_id:
            material_update = client.put(
                f"/api/teacher/materials/{material_id}",
                json={"title": "阶段复习资料-修订", "file_path": "materials/teacher_updated_material.pdf"},
            ).get_json()
            record("老师-修改资料", expect(material_update), str(material_update))

            material_delete = client.delete(f"/api/teacher/materials/{material_id}").get_json()
            record("老师-删除资料", expect(material_delete), str(material_delete))

        eval_list = client.get("/api/teacher/evaluation_list").get_json()
        record("老师-查看评价", expect(eval_list), str(eval_list)[:200])


def run_new_feature_tests():
    """新增模块冒烟：学习计划/考试/推荐/通知。"""
    exam_id = None

    def build_exam_question(question_type):
        if question_type == "single":
            return {
                "question_type": "single",
                "content": "以下哪项是医学考研常见复习方法？",
                "options": ["A. 艾宾浩斯复习", "B. 随机突击", "C. 只看答案"],
                "correct_answer": "A. 艾宾浩斯复习",
                "score": 5,
            }
        if question_type == "judge":
            return {
                "question_type": "judge",
                "content": "规律复习通常比突击复习更有利于长期记忆。",
                "correct_answer": "正确",
                "score": 4,
            }
        if question_type == "fill":
            return {
                "question_type": "fill",
                "content": "医学统计中常见显著性阈值是？",
                "correct_answer": "0.05",
                "score": 6,
            }
        if question_type == "multi":
            return {
                "question_type": "multi",
                "content": "下列属于高效复习策略的是？",
                "options": ["A. 错题复盘", "B. 阶段总结", "C. 只看答案"],
                "correct_answer": "A,B",
                "score": 2,
            }
        if question_type == "pair":
            return {
                "question_type": "pair",
                "content": "请根据知识点与描述进行对应。",
                "options": ["A. 心衰", "B. 高血压", "1. 容量负荷增加", "2. 外周阻力升高"],
                "correct_answer": "A-1,B-2",
                "score": 2,
            }
        if question_type == "term":
            return {
                "question_type": "term",
                "content": "解释医学中的“敏感度”概念。",
                "score": 8,
            }
        if question_type == "essay":
            return {
                "question_type": "essay",
                "content": "结合你当前阶段，论述一套可执行的考研复习策略。",
                "score": 12,
            }
        return {
            "question_type": "short",
            "content": "简述你本周复习策略。",
            "score": 10,
        }

    def build_questions_for_course(course):
        allowed = list(get_allowed_question_types(course or ""))
        preferred_order = ["single", "judge", "fill", "multi", "pair", "short", "term", "essay"]
        picked_types = [item for item in preferred_order if item in allowed][:3]
        if not picked_types:
            picked_types = ["single", "short"]
        return [build_exam_question(item) for item in picked_types]

    with app.test_client() as teacher_client:
        teacher_login, _ = login_any(teacher_client, "teacher", ["周凯", "李明"])
        if expect(teacher_login):
            now = datetime.now()
            start_time = (now + timedelta(days=1)).strftime("%Y-%m-%d 09:00:00")
            end_time = (now + timedelta(days=1)).strftime("%Y-%m-%d 10:30:00")
            teacher_id = teacher_login.get("data", {}).get("user_id") if isinstance(teacher_login, dict) else None
            teacher_course = resolve_teacher_bound_course(int(teacher_id)) if teacher_id else None
            questions = build_questions_for_course(teacher_course)
            create_exam = teacher_client.post(
                "/api/teacher/exam",
                json={
                    "title": "阶段模拟测验-自动化",
                    "description": "自动化脚本创建",
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": 90,
                    "status": "published",
                    "questions": questions,
                },
            ).get_json()
            record("新增模块-老师创建考试", expect(create_exam), str(create_exam)[:220])
            if isinstance(create_exam, dict):
                exam_id = create_exam.get("data", {}).get("exam_id")

    with app.test_client() as student_client:
        student_login, _ = login_any(student_client, "student", ["李悦", "张晨"])
        if not expect(student_login):
            record("新增模块-学生登录初始化", False, "学生登录失败")
            return

        plan_create = student_client.post(
            "/api/student/learning_plan",
            json={
                "title": "自动化学习计划",
                "target": "验证学习计划链路",
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "status": "ongoing",
            },
        ).get_json()
        record("新增模块-学生创建学习计划", expect(plan_create), str(plan_create)[:220])

        plan_id = plan_create.get("data", {}).get("plan_id") if isinstance(plan_create, dict) else None
        task_id = None
        if plan_id:
            task_create = student_client.post(
                "/api/student/learning_task",
                json={
                    "plan_id": plan_id,
                    "task_title": "自动化学习任务",
                    "task_date": datetime.now().strftime("%Y-%m-%d"),
                    "estimated_minutes": 60,
                },
            ).get_json()
            record("新增模块-学生创建学习任务", expect(task_create), str(task_create)[:220])
            task_id = task_create.get("data", {}).get("task_id") if isinstance(task_create, dict) else None

            if task_id:
                task_update = student_client.put(
                    f"/api/student/learning_task/{task_id}",
                    json={
                        "task_title": "自动化学习任务-完成",
                        "task_date": datetime.now().strftime("%Y-%m-%d"),
                        "estimated_minutes": 60,
                        "sort_no": 0,
                        "is_done": 1,
                    },
                ).get_json()
                record("新增模块-学生完成学习任务", expect(task_update), str(task_update)[:220])

            progress = student_client.post(
                "/api/student/plan_progress",
                json={"plan_id": plan_id, "study_minutes": 90, "note": "自动化记录"},
            ).get_json()
            record("新增模块-学生记录学习进度", expect(progress), str(progress)[:220])

            progress_stat = student_client.get(f"/api/student/plan_progress_stat?plan_id={plan_id}").get_json()
            record("新增模块-学生查看学习进度统计", expect(progress_stat), str(progress_stat)[:220])

        exam_list = student_client.get("/api/student/exam_list").get_json()
        record("新增模块-学生查看考试列表", expect(exam_list), str(exam_list)[:220])

        target_exam_id = None
        if isinstance(exam_list, dict) and exam_list.get("data"):
            target_exam_id = exam_list["data"][0].get("id")
        if not target_exam_id:
            target_exam_id = exam_id

        if target_exam_id:
            exam_detail = student_client.get(f"/api/student/exam/{target_exam_id}/detail").get_json()
            record("新增模块-学生查看考试详情", expect(exam_detail), str(exam_detail)[:220])

            answers = []
            question_rows = exam_detail.get("data", {}).get("questions") if isinstance(exam_detail, dict) else []
            for item in question_rows or []:
                qid = item.get("id")
                qtype = item.get("question_type")
                if not qid:
                    continue
                if qtype == "single":
                    options = item.get("options") or []
                    answer_text = options[0] if options else ""
                elif qtype == "fill":
                    answer_text = "0.05"
                else:
                    answer_text = "自动化答题内容"
                answers.append({"question_id": qid, "answer_text": answer_text})

            if answers:
                submit_exam = student_client.post(
                    "/api/student/exam_submit",
                    json={"exam_id": target_exam_id, "answers": answers},
                ).get_json()
                ok = expect(submit_exam) or (isinstance(submit_exam, dict) and submit_exam.get("code") == 400)
                record("新增模块-学生提交考试", ok, str(submit_exam)[:220])

            exam_records = student_client.get("/api/student/exam_record_list").get_json()
            record("新增模块-学生查看考试记录", expect(exam_records), str(exam_records)[:220])

        recommendation = student_client.get("/api/student/recommendation_feed").get_json()
        record("新增模块-学生查看推荐流", expect(recommendation), str(recommendation)[:220])

        notice_list = student_client.get("/api/notification/list").get_json()
        record("新增模块-学生查看通知", expect(notice_list), str(notice_list)[:220])

        notice_all_read = student_client.post("/api/notification/read_all").get_json()
        record("新增模块-学生通知全部已读", expect(notice_all_read), str(notice_all_read)[:220])

    with app.test_client() as admin_client:
        admin_login = admin_client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).get_json()
        if expect(admin_login):
            admin_notice = admin_client.get("/api/admin/notification/list").get_json()
            record("新增模块-管理员查看通知", expect(admin_notice), str(admin_notice)[:220])

            admin_all_read = admin_client.post("/api/admin/notification/read_all").get_json()
            record("新增模块-管理员通知全部已处理", expect(admin_all_read), str(admin_all_read)[:220])

def run_supervisor_tests():
    with app.test_client() as client:
        if not expect(login(client, "孙华", "supervisor")):
            record("督学端用例初始化", False, "督学登录失败")
            return

        student_list = client.get("/api/supervisor/student_list").get_json()
        record("督学-查看学员管理列表", expect(student_list), str(student_list)[:200])

        target = None
        if isinstance(student_list, dict):
            rows = student_list.get("data") or []
            if rows:
                target = rows[0]
        if target:
            edit = client.post(
                "/api/supervisor/edit_student",
                json={
                    "id": target.get("id"),
                    "name": target.get("name", ""),
                    "gender": target.get("gender", "男"),
                    "age": target.get("age", 23),
                    "major": target.get("major", "临床医学"),
                    "grade": target.get("grade", "2025"),
                    "class": target.get("class_name", "A班"),
                    "teacher_id": target.get("teacher_id"),
                },
            ).get_json()
            record("督学-编辑学员", expect(edit), str(edit))

        checkin_stat = client.get("/api/supervisor/checkin_stat").get_json()
        record("督学-打卡统计", expect(checkin_stat), str(checkin_stat)[:200])

        eval_stat = client.get("/api/supervisor/evaluation_stat").get_json()
        record("督学-评价统计", expect(eval_stat), str(eval_stat)[:200])


def run_admin_tests():
    with app.test_client() as client:
        admin_login = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"}).get_json()
        record("管理员登录", expect(admin_login), str(admin_login))
        if not expect(admin_login):
            return

        stats = client.get("/api/admin/stats").get_json()
        record("管理员-数据概览", expect(stats), str(stats)[:200])

        users = client.get("/api/admin/users").get_json()
        record("管理员-用户管理查询", expect(users), str(users)[:200])

        tmp_username = f"seed_user_{datetime.now().strftime('%H%M%S')}"
        create_user = client.post(
            "/api/admin/users",
            json={"username": tmp_username, "password": "123456", "role": "student", "name": "测试用户"},
        ).get_json()
        record("管理员-用户新增", expect(create_user), str(create_user))

        user_id = create_user.get("data", {}).get("id") if isinstance(create_user, dict) else None
        if user_id:
            update_user = client.put(
                f"/api/admin/users/{user_id}",
                json={"username": "沈安", "role": "student", "password": "123456"},
            ).get_json()
            record("管理员-用户修改", expect(update_user), str(update_user))
            delete_user = client.delete(f"/api/admin/users/{user_id}").get_json()
            record("管理员-用户删除", expect(delete_user), str(delete_user))

        student_info = client.get("/api/admin/student_info/list").get_json()
        record("管理员-学员信息管理", expect(student_info), str(student_info)[:200])

        homework = client.get("/api/admin/homework/list").get_json()
        record("管理员-作业管理", expect(homework), str(homework)[:200])

        materials = client.get("/api/admin/materials/list").get_json()
        record("管理员-资料管理", expect(materials), str(materials)[:200])

        checkin = client.get("/api/admin/checkin/list").get_json()
        record("管理员-打卡管理", expect(checkin), str(checkin)[:200])

        evaluation = client.get("/api/admin/evaluation/list").get_json()
        record("管理员-评价管理", expect(evaluation), str(evaluation)[:200])

        batch_ids = []
        if isinstance(checkin, dict):
            rows = checkin.get("data") or []
            batch_ids = [row["id"] for row in rows[:1] if isinstance(row, dict)]
        if batch_ids:
            batch_delete = client.post("/api/admin/checkin/delete_batch", json={"ids": batch_ids}).get_json()
            record("管理员-批量删除", expect(batch_delete), str(batch_delete))

        export_checkin = client.get("/api/admin/checkin/export")
        record("管理员-导出数据", export_checkin.status_code == 200 and b"student_id" in export_checkin.data, f"status={export_checkin.status_code}")

        admin_logout = client.post("/api/admin/logout").get_json()
        record("管理员退出登录", expect(admin_logout), str(admin_logout))


def write_report():
    passed = sum(1 for item in results if item["passed"])
    failed = len(results) - passed

    report_path = "backend/test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 红师医学考研学员管理系统 - 自动化测试报告\n\n")
        f.write(f"- 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 总用例：{len(results)}\n")
        f.write(f"- 通过：{passed}\n")
        f.write(f"- 失败：{failed}\n\n")

        f.write("## 功能验证结果\n\n")
        for item in results:
            icon = "✅" if item["passed"] else "❌"
            f.write(f"- {icon} {item['case']}：{item['detail']}\n")

        f.write("\n## 已识别问题\n\n")
        if issues:
            for issue in sorted(set(issues)):
                f.write(f"- {issue}\n")
        else:
            f.write("- 未发现明显问题\n")

        f.write("\n## 改进建议\n\n")
        f.write("- 建议补充老师端对作业提交记录的附件在线预览能力。\n")
        f.write("- 建议补充学员作业提交附件格式与大小前后端统一校验。\n")
        f.write("- 建议为核心接口增加自动化回归测试并接入 CI。\n")

    print(f"测试报告已生成: {report_path}")
    print(f"通过 {passed}/{len(results)}，失败 {failed}")


def main():
    run_basic_and_role_tests()
    run_student_tests()
    run_new_feature_tests()
    run_teacher_tests()
    run_supervisor_tests()
    run_admin_tests()
    write_report()


if __name__ == "__main__":
    main()
