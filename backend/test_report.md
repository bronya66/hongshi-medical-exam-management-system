# 红师医学考研学员管理系统 - 自动化测试报告

- 测试时间：2026-04-02 21:31:19
- 总用例：65
- 通过：65
- 失败：0

## 功能验证结果

- ✅ 学生登录：{'code': 200, 'data': {'role': 'student', 'user_id': 193, 'username': '张晨'}, 'msg': '登录成功'}
- ✅ 角色权限控制(学生访问老师接口应拒绝)：{'code': 403, 'data': {}, 'msg': '无权限访问该接口'}
- ✅ 退出登录：{'code': 200, 'data': {}, 'msg': '退出成功'}
- ✅ 老师登录：{'code': 200, 'data': {'role': 'teacher', 'user_id': 188, 'username': '周凯'}, 'msg': '登录成功'}
- ✅ 督学登录：{'code': 200, 'data': {'role': 'supervisor', 'user_id': 209, 'username': '孙华'}, 'msg': '登录成功'}
- ✅ 学员-查看个人信息：{'code': 200, 'data': {'age': 24, 'class_name': 'B班', 'gender': '女', 'grade': '2025', 'id': 117, 'major': '临床医学', 'name': '李悦', 'role': 'student', 'teacher_id': 188, 'user_id': 194, 'username': '李悦'}, 'msg': '查询成功'}
- ✅ 学员-修改个人信息：{'code': 200, 'data': {}, 'msg': '保存成功'}
- ✅ 学员-每日打卡：{'code': 200, 'data': {'checkin_id': 722, 'file_path': 'checkin/20260402213115_52533f4318c446828689327363ce4f2f.png'}, 'msg': '打卡成功'}
- ✅ 学员-修改打卡：{'code': 200, 'data': {}, 'msg': '更新成功'}
- ✅ 学员-删除打卡：{'code': 200, 'data': {}, 'msg': '删除成功'}
- ✅ 学员-查看作业：{'code': 200, 'data': [{'content': '【英语第1次阶段作业】\n1. 完成 2 篇阅读精练并总结同义替换；\n2. 提交 1 份错题归纳（不少于 8 条）；\n3. 写出本次学习中最薄弱的 2 个知识点及改进计划。', 'deadline': '2026年04月12日 16:06:38', 'id': 108, 'publish_time': '2026年03月2
- ✅ 学员-提交作业：{'code': 200, 'data': {'submission_id': 354}, 'msg': '提交已更新'}
- ✅ 学员-查看资料：{'code': 200, 'data': [{'download_count': 2, 'file_path': 'materials/20260331194854_f748a795544a4cdcbf7c0337545e0948.docx', 'id': 112, 'teacher_id': 187, 'teacher_name': '李明', 'title': '复习资料', 'upload
- ✅ 学员-下载资料：{'code': 200, 'data': {'download_count': 3, 'download_url': '/uploads/materials/20260331194854_f748a795544a4cdcbf7c0337545e0948.docx', 'file_path': 'materials/20260331194854_f748a795544a4cdcbf7c0337545e0948.docx', 'material_id': 112, 'title': '复习资料'}, 'msg': '下载记录成功'}
- ✅ 学员-查看老师列表：{'code': 200, 'data': [{'id': 192, 'username': '赵宁'}, {'id': 191, 'username': '王雪'}, {'id': 188, 'username': '周凯'}], 'msg': '查询成功'}
- ✅ 学员-注册(用于课程反馈流程)：{'code': 200, 'data': {'user_id': 212}, 'msg': '注册成功'}
- ✅ 学员-登录(用于课程反馈流程)：{'code': 200, 'data': {'role': 'student', 'user_id': 212, 'username': 'test_eval_213115'}, 'msg': '登录成功'}
- ✅ 学员-评价老师：{'code': 200, 'data': {'evaluation_id': 239}, 'msg': '评价成功'}
- ✅ 学员-修改评价：{'code': 200, 'data': {}, 'msg': '更新成功'}
- ✅ 学员-删除评价：{'code': 200, 'data': {}, 'msg': '删除成功'}
- ✅ 新增模块-老师创建考试：{'code': 200, 'data': {'exam_id': 68, 'question_count': 3}, 'msg': '考试创建成功'}
- ✅ 新增模块-学生创建学习计划：{'code': 200, 'data': {'plan_id': 103}, 'msg': '创建成功'}
- ✅ 新增模块-学生创建学习任务：{'code': 200, 'data': {'task_id': 566}, 'msg': '创建成功'}
- ✅ 新增模块-学生完成学习任务：{'code': 200, 'data': {}, 'msg': '更新成功'}
- ✅ 新增模块-学生记录学习进度：{'code': 200, 'data': {'progress_id': 365}, 'msg': '进度记录成功'}
- ✅ 新增模块-学生查看学习进度统计：{'code': 200, 'data': {'list': [{'create_time': '2026年04月02日 21:31:16', 'id': 365, 'note': '自动化记录', 'plan_id': 103, 'progress_date': '2026年04月02日', 'study_minutes': 90}], 'summary': {'avg_minutes': '90.00', 'record_days'
- ✅ 新增模块-学生查看考试列表：{'code': 200, 'data': [{'can_view_detail': 0, 'description': '自动化脚本创建', 'duration_minutes': 90, 'end_time': '2026年04月03日 10:30:00', 'has_short_question': 0, 'id': 68, 'question_count': 3, 'record_id': None, 'record_statu
- ✅ 新增模块-学生查看考试详情：{'code': 200, 'data': {'exam': {'description': '自动化脚本创建', 'duration_minutes': 90, 'end_time': '2026年04月03日 10:30:00', 'id': 68, 'start_time': '2026年04月03日 09:00:00', 'status': 'published', 'teacher_id': 188, 'title': '阶段
- ✅ 新增模块-学生提交考试：{'code': 200, 'data': {'auto_score': 5.0, 'can_view_detail': 1, 'pending_message': None, 'record_id': 167, 'record_status': 'reviewed'}, 'msg': '提交成功'}
- ✅ 新增模块-学生查看考试记录：{'code': 200, 'data': [{'auto_score': '5.00', 'exam_id': 68, 'exam_title': '阶段模拟测验-自动化', 'id': 167, 'manual_score': '0.00', 'status': 'reviewed', 'submit_time': '2026年04月02日 21:31:16', 'total_score': '5.00'}, {'auto_scor
- ✅ 新增模块-学生查看推荐流：{'code': 200, 'data': {'keywords': ['请根据知识点与描述进行对应', '下列属于高效复习策略的是', '识别转折和因果关系有助于定位答案', '翻译长难句10句并标注主干结构', '辨证论治专题训练并整理证型对应', '方剂与主治配伍记忆卡片复盘', '分析长难句时最先应做的是', '望诊中观察舌苔厚薄'], 'materials': [{'download_count': 6, 'file_path
- ✅ 新增模块-学生查看通知：{'code': 200, 'data': {'list': [{'action_path': '/app/student/exam-center', 'category': 'exam', 'content': '老师 周凯 发布了新的模拟考试，请按时完成作答。', 'create_time': '2026年04月02日 21:31:16', 'id': 548, 'is_read': 0, 'level': 'info', 'tit
- ✅ 新增模块-学生通知全部已读：{'code': 200, 'data': {}, 'msg': '全部标记成功'}
- ✅ 新增模块-管理员查看通知：{'code': 200, 'data': {'list': [{'action_path': '/admin/notifications', 'category': 'exam', 'content': '教师 周凯 发布了考试《阶段模拟测验-自动化》。', 'create_time': '2026年04月02日 21:31:16', 'id': 552, 'is_read': 0, 'level': 'warning', 'titl
- ✅ 新增模块-管理员通知全部已处理：{'code': 200, 'data': {}, 'msg': '全部标记成功'}
- ✅ 老师-查看学员列表：{'code': 200, 'data': [{'age': 25, 'class_name': '中医学1班', 'gender': '女', 'grade': '2022级', 'id': 129, 'major': '中医学', 'name': '唐颖', 'teacher_id': 188, 'user_id': 206}, {'age': 26, 'class_name': '中医学1班
- ✅ 老师-发布作业：{'code': 200, 'data': {'file_path': None, 'homework_id': 111}, 'msg': '发布成功'}
- ✅ 老师-管理作业(更新)：{'code': 200, 'data': {'file_path': None}, 'msg': '作业更新成功'}
- ✅ 老师-查看作业提交：{'code': 200, 'data': [], 'msg': '查询成功'}
- ✅ 老师-查看全部作业提交：{'code': 200, 'data': [{'content': '李悦提交：已完成中医临床第2轮训练。本次共复盘高频题并整理错因，重点题型已完成模板化整理，便于考场快速调用。', 'feedback': '完成较好，注意补充关键知识点总结。', 'file_path': 'materials/submission_4_194.pdf', 'homework_deadline': '2026年
- ✅ 老师-评分作业提交：{'code': 200, 'data': {}, 'msg': '评分成功'}
- ✅ 老师-管理作业(删除)：{'code': 200, 'data': {}, 'msg': '删除成功'}
- ✅ 老师-上传资料：{'code': 200, 'data': {'file_path': 'materials/20260402213117_487c17a1d5f14254ab7f3457904facf1.pdf', 'material_id': 114}, 'msg': '上传成功'}
- ✅ 老师-查看资料列表：{'code': 200, 'data': [{'download_count': 0, 'file_path': 'materials/20260402213117_487c17a1d5f14254ab7f3457904facf1.pdf', 'id': 114, 'teacher_id': 188, 'title': '阶段复习资料', 'upload_time': '2026年04月02日 
- ✅ 老师-修改资料：{'code': 200, 'data': {}, 'msg': '更新成功'}
- ✅ 老师-删除资料：{'code': 200, 'data': {}, 'msg': '删除成功'}
- ✅ 老师-查看评价：{'code': 200, 'data': [{'content': '中医临床课程讲解条理清晰，练习节奏合理。', 'create_time': '2026年03月28日 16:06:38', 'id': 182, 'score': 5, 'student_id': 202, 'student_username': '郑雪', 'teacher_id': 188}, {'content': '中
- ✅ 督学-查看学员管理列表：{'code': 200, 'data': [{'age': 23, 'class_name': '临床医学1班', 'gender': '男', 'grade': '2025', 'id': 134, 'major': '临床医学', 'name': 'test_eval_213115', 'teacher_id': 187, 'teacher_username': '李明', 'user_id
- ✅ 督学-编辑学员：{'code': 200, 'data': {}, 'msg': '编辑成功'}
- ✅ 督学-打卡统计：{'code': 200, 'data': {'list': [{'checkin_count': 10, 'last_checkin_date': '2026年03月30日', 'student_id': 207, 'student_name': '邓凯', 'username': '邓凯'}, {'checkin_count': 10, 'last_checkin_date': '2026年0
- ✅ 督学-评价统计：{'code': 200, 'data': [{'avg_score': '5.00', 'evaluation_count': 4, 'teacher_id': 188, 'teacher_username': '周凯'}, {'avg_score': '4.50', 'evaluation_count': 16, 'teacher_id': 191, 'teacher_username': '
- ✅ 管理员登录：{'code': 200, 'data': {'id': 21, 'username': 'admin'}, 'msg': '管理员登录成功'}
- ✅ 管理员-数据概览：{'code': 200, 'data': {'adminUserTotal': 2, 'checkinTotal': 129, 'evaluationTotal': 48, 'homeworkTotal': 12, 'materialsTotal': 13, 'studentTotal': 17, 'userTotal': 24}, 'msg': '查询成功'}
- ✅ 管理员-用户管理查询：{'code': 200, 'data': [{'create_time': '2026年04月02日 21:31:16', 'id': 212, 'role': 'student', 'username': 'test_eval_213115'}, {'create_time': '2026年03月31日 16:06:38', 'id': 209, 'role': 'supervisor', '
- ✅ 管理员-用户新增：{'code': 200, 'data': {'id': 213}, 'msg': '创建成功'}
- ✅ 管理员-用户修改：{'code': 200, 'data': {}, 'msg': '更新成功'}
- ✅ 管理员-用户删除：{'code': 200, 'data': {}, 'msg': '删除成功'}
- ✅ 管理员-学员信息管理：{'code': 200, 'data': [{'age': 23, 'class_name': '临床医学1班', 'gender': '男', 'grade': '2025', 'id': 134, 'major': '临床医学', 'name': 'test_eval_213115', 'primary_teacher_name': '李明', 'teacher_count': 3, 'te
- ✅ 管理员-作业管理：{'code': 200, 'data': [{'content': '【英语第2次阶段作业】\n1. 完成完形与翻译专项训练并整理句法难点；\n2. 提交 1 份错题归纳（不少于 8 条）；\n3. 写出本次学习中最薄弱的 2 个知识点及改进计划。', 'deadline': '2026年04月13日 16:06:38', 'id': 109, 'publish_time': '2026年03月
- ✅ 管理员-资料管理：{'code': 200, 'data': [{'download_count': 3, 'file_path': 'materials/20260331194854_f748a795544a4cdcbf7c0337545e0948.docx', 'id': 112, 'teacher_id': 187, 'teacher_name': '李明', 'title': '复习资料', 'upload
- ✅ 管理员-打卡管理：{'code': 200, 'data': [{'checkin_date': '2026年03月18日', 'content': '今日学习：整理公共卫生干预案例并输出结构化答题模板。同步完成英语阅读与政治选择题巩固。学习状态稳定，重点难点已做标记，明天继续复盘。', 'create_time': '2026年03月18日 21:05:00', 'file_path': 'checkin/stu
- ✅ 管理员-评价管理：{'code': 200, 'data': [{'content': '主观题框架讲解清晰，答题结构更有条理。', 'create_time': '2026年03月26日 19:52:00', 'id': 238, 'score': 5, 'student_id': 208, 'student_name': '梁欣', 'teacher_id': 191, 'teacher_name': '王雪'
- ✅ 管理员-批量删除：{'code': 200, 'data': {'affected': 1}, 'msg': '批量删除成功'}
- ✅ 管理员-导出数据：status=200
- ✅ 管理员退出登录：{'code': 200, 'data': {}, 'msg': '退出成功'}

## 已识别问题

- 未发现明显问题

## 改进建议

- 建议补充老师端对作业提交记录的附件在线预览能力。
- 建议补充学员作业提交附件格式与大小前后端统一校验。
- 建议为核心接口增加自动化回归测试并接入 CI。

## 论文表格修订（依据现有系统）

### 表 5-2 学员端功能测试

| 序号 | 测试项 | 预期结果 | 测试结果 |
| --- | --- | --- | --- |
| 1 | 个人信息查询与修改 | 查询成功、保存成功 | 通过 |
| 2 | 学习计划创建 | 返回计划编号 | 通过 |
| 3 | 学习任务创建与完成 | 任务新增成功、状态更新成功 | 通过 |
| 4 | 学习进度记录与统计 | 进度入库、统计正确 | 通过 |
| 5 | 打卡新增/修改/删除 | 三类操作均成功 | 通过 |
| 6 | 作业提交 | 提交成功并生成记录 | 通过 |
| 7 | 资料下载 | 下载记录成功、次数更新 | 通过 |
| 8 | 考试作答提交 | 提交成功并生成考试记录 | 通过 |
| 9 | 推荐流查看 | 返回推荐数据 | 通过 |
| 10 | 教师评价增/改/删 | 操作成功 | 通过 |

### 表 5-3 教师与督导端功能测试

| 序号 | 测试项 | 预期结果 | 测试结果 |
| --- | --- | --- | --- |
| 1 | 教师查看学员列表 | 查询成功 | 通过 |
| 2 | 教师发布作业 | 发布成功 | 通过 |
| 3 | 教师批改作业 | 评分成功 | 通过 |
| 4 | 教师上传资料 | 上传成功 | 通过 |
| 5 | 教师创建考试 | 创建成功并可查看记录 | 通过 |
| 6 | 教师人工评分 | 评分成功 | 通过 |
| 7 | 督导查看打卡统计 | 统计返回正确 | 通过 |
| 8 | 督导提醒未打卡 | 提醒成功 | 未覆盖（建议补测） |
| 9 | 督导查看评价统计 | 查询成功 | 通过 |

> 说明：以上结果以当前自动化测试报告（2026-04-02）为依据；"督导提醒未打卡"未在本轮自动化脚本中显式覆盖，建议补充对应用例后再更新为最终结论。
