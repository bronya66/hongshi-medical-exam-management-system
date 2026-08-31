import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, insert_and_get_id, query_one

USER_PASSWORD = "123456"
ADMIN_PASSWORD = "admin123"

USER_PASSWORD_HASH = generate_password_hash(USER_PASSWORD)
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

SUPERVISOR = {"username": "孙华", "name": "孙华"}
ADMIN = {"username": "管理员"}

RNG = random.Random(20260320)

PROFESSIONAL_COURSES = [
    "西医临床",
    "中医临床",
    "口腔医学",
    "其他类（护理学、医学技术、基础医学、公共卫生等）",
]

MAJOR_BY_COURSE = {
    "西医临床": "临床医学",
    "中医临床": "中医学",
    "口腔医学": "口腔医学",
    "其他类（护理学、医学技术、基础医学、公共卫生等）": "医学技术",
}

CLASS_BY_COURSE = {
    "西医临床": "临床医学1班",
    "中医临床": "中医学1班",
    "口腔医学": "口腔医学1班",
    "其他类（护理学、医学技术、基础医学、公共卫生等）": "医技综合1班",
}

STUDENT_NAME_POOL = [
    ("张晨", "male"),
    ("李悦", "female"),
    ("王浩", "male"),
    ("陈琳", "female"),
    ("刘涛", "male"),
    ("赵敏", "female"),
    ("孙磊", "male"),
    ("周宁", "female"),
    ("吴凡", "male"),
    ("郑雪", "female"),
    ("高远", "male"),
    ("何静", "female"),
    ("许博", "male"),
    ("唐颖", "female"),
    ("邓凯", "male"),
    ("梁欣", "female"),
]

COURSE_HOMEWORK_TASKS = {
    "西医临床": [
        "完成循环系统高频考点导图并整理 20 道错题",
        "按病例模板完成 2 例鉴别诊断书写",
        "复盘近 3 年真题中的内科综合题并标注易错点",
    ],
    "中医临床": [
        "完成八纲辨证专题笔记并配套 30 道选择题",
        "围绕常见证型完成方剂配伍对照表",
        "整理舌脉辨证高频混淆点并写出辨证思路",
    ],
    "口腔医学": [
        "完成龋病与牙周病章节对比总结及病例题训练",
        "按规范书写口腔检查记录并完成影像判读练习",
        "复盘近年口腔外科常考操作流程与并发症处理",
    ],
    "其他类（护理学、医学技术、基础医学、公共卫生等）": [
        "完成护理程序与医学统计基础题型训练",
        "围绕流行病学指标完成计算题专项复盘",
        "整理公共卫生干预案例并输出结构化答题模板",
    ],
    "政治": [
        "完成马原高频选择题 50 题并归类错因",
        "整理近代史时间线与关键事件因果关系",
        "输出当代中国理论框架思维导图并进行口述复盘",
    ],
    "英语": [
        "完成 2 篇阅读精练并总结同义替换",
        "完成完形与翻译专项训练并整理句法难点",
        "按考研作文模板写 1 篇应用文并自评修改",
    ],
}

CHECKIN_PROGRESS_SNIPPETS = [
    "今日按计划完成核心任务，并做了二次错题订正。",
    "学习状态稳定，重点难点已做标记，明天继续复盘。",
    "完成限时训练后复查薄弱点，正确率较昨日有提升。",
    "已将高频考点整理成卡片，晚上进行回忆巩固。",
]

COURSE_MATERIAL_TITLES = {
    "西医临床": [
        "西医临床系统复习讲义（循环+呼吸）",
        "西医临床高频病例分析与答题模板",
        "西医临床易错考点速记清单",
    ],
    "中医临床": [
        "中医临床辨证思路总表（八纲+脏腑）",
        "中医方剂配伍与常见证型对照",
        "中医临床高频论述题框架整理",
    ],
    "口腔医学": [
        "口腔医学龋病与牙周病重点汇编",
        "口腔影像判读与病例要点笔记",
        "口腔外科常见并发症处理流程",
    ],
    "其他类（护理学、医学技术、基础医学、公共卫生等）": [
        "护理程序与基础护理考点清单",
        "医学统计与流行病学核心公式手册",
        "公共卫生案例分析与答题模板",
    ],
    "政治": [
        "政治马原高频选择题精讲",
        "政治近代史时间轴与重点事件",
        "政治主观题答题逻辑模板",
    ],
    "英语": [
        "英语阅读同义替换与长难句拆解",
        "英语完形翻译高频词组与句型",
        "英语作文模板与高分表达积累",
    ],
}

LEARNING_TASK_TEMPLATES = {
    "政治": [
        "马原选择题30题精练并错因归类",
        "近代史章节主线复盘与时间轴默写",
    ],
    "英语": [
        "阅读2篇限时训练并整理同义替换",
        "翻译长难句10句并标注主干结构",
    ],
    "西医临床": [
        "内科高频考点复盘并完成病例题2道",
        "生理病理易错点二次订正与口述总结",
    ],
    "中医临床": [
        "辨证论治专题训练并整理证型对应",
        "方剂与主治配伍记忆卡片复盘",
    ],
    "口腔医学": [
        "牙周与龋病鉴别要点训练",
        "口腔病例书写规范练习与自查",
    ],
    "其他类（护理学、医学技术、基础医学、公共卫生等）": [
        "护理程序应用题训练与步骤复盘",
        "流行病学指标计算题专项练习",
    ],
}

COURSE_EXAM_THEMES = {
    "西医临床": ["系统强化诊断卷", "病例综合提升卷", "高频考点冲刺卷"],
    "中医临床": ["辨证论治强化卷", "方剂与证型综合卷", "临床思维提升卷"],
    "口腔医学": ["口腔综合能力训练卷", "牙周与修复专题卷", "病例分析强化卷"],
    "其他类（护理学、医学技术、基础医学、公共卫生等）": ["护理与公卫综合卷", "医技基础能力卷", "统计与流调专项卷"],
    "政治": ["政治选择题强化卷", "政治主客观综合卷", "时政与理论冲刺卷"],
    "英语": ["英语阅读翻译能力卷", "英语综合提分卷", "英语冲刺模拟卷"],
}

QUESTION_TYPE_LABEL = {
    "single": "单选",
    "multi": "多选",
    "pair": "配伍",
    "judge": "判断",
    "fill": "填空",
    "term": "名词解释",
    "short": "简答",
    "essay": "论述",
}


def build_homework_content(course, hw_no):
    tasks = COURSE_HOMEWORK_TASKS.get(course, ["完成章节训练并总结错题"])
    task = tasks[(hw_no - 1) % len(tasks)]
    return (
        f"【{course}第{hw_no}次阶段作业】\n"
        f"1. {task}；\n"
        "2. 提交 1 份错题归纳（不少于 8 条）；\n"
        "3. 写出本次学习中最薄弱的 2 个知识点及改进计划。"
    )


def build_material_title(course, material_no):
    titles = COURSE_MATERIAL_TITLES.get(course, [f"{course}阶段复习资料"])
    base = titles[(material_no - 1) % len(titles)]
    return f"{base}（第{material_no}版）"


def build_learning_task_title(subject, round_no):
    templates = LEARNING_TASK_TEMPLATES.get(subject, [f"{subject}章节学习任务"])
    base = templates[(round_no - 1) % len(templates)]
    return f"{base}"


def build_exam_title_and_description(course, exam_questions, idx, now):
    themes = COURSE_EXAM_THEMES.get(course, ["阶段测评卷"])
    theme = themes[(idx - 1) % len(themes)]

    yymm = now.strftime("%Y.%m")
    title = f"{yymm} {course}{theme}"

    type_labels = []
    for item in exam_questions:
        label = QUESTION_TYPE_LABEL.get(item.get("question_type"), item.get("question_type"))
        if label and label not in type_labels:
            type_labels.append(label)
    type_summary = "、".join(type_labels[:4]) if type_labels else "综合题型"

    focus_points = []
    for item in exam_questions[:2]:
        content = str(item.get("content") or "").replace("？", "").replace("。", "").strip()
        if not content:
            continue
        focus_points.append(content[:16])
    focus_summary = "、".join(focus_points) if focus_points else "核心考点"

    description = f"{course}阶段测评，覆盖{type_summary}，重点聚焦：{focus_summary}。"
    return title, description


def build_submission_content(course, student_name, hw_no, homework_title, homework_content, student_id):
    style_templates = [
        "先做框架再回填细节",
        "先复盘错题再做同类迁移",
        "按考场答题时序进行限时训练",
    ]
    weak_points = [
        "鉴别诊断层次", "高频概念边界", "主观题关键词覆盖", "题干关键信息提取"
    ]
    reflections = [
        "错题已按知识点分类，二次作答后正确率提升。",
        "重点题型已完成模板化整理，便于考场快速调用。",
        "对薄弱章节补充了思维导图与记忆卡片。",
    ]
    reflection = reflections[(student_id + hw_no) % len(reflections)]
    style = style_templates[(student_id + hw_no) % len(style_templates)]
    weak = weak_points[(student_id + hw_no) % len(weak_points)]
    requirement = (str(homework_content or "").split("\n")[0] or "完成阶段训练任务").strip()
    return (
        f"{student_name}提交：已完成《{homework_title}》训练。"
        f"根据作业要求“{requirement}”，采用“{style}”策略推进；"
        f"当前主要改进点为{weak}。"
        f"本次共复盘{course}高频题并整理错因，{reflection}"
    )


def write_submission_attachment(course, student_name, hw_no, homework_id, student_id, homework_title, homework_content):
    """为作业提交生成真实附件文本并返回相对路径。"""
    target_dir = BACKEND_DIR / "uploads" / "homework"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"submission_hw{homework_id}_stu{student_id}_r{hw_no}.txt"
    file_path = target_dir / filename
    methods = ["对照表法", "病例链路法", "错因标签法"]
    method = methods[(student_id + hw_no) % len(methods)]
    file_text = (
        f"学员：{student_name}\n"
        f"课程：{course}\n"
        f"作业标题：{homework_title}\n"
        f"作业轮次：第{hw_no}轮\n"
        "\n"
        "作业原始要求\n"
        f"{(homework_content or '').strip()}\n"
        "\n"
        "一、完成情况\n"
        f"- 已完成{course}高频考点复盘与错题归因。\n"
        f"- 重点补强了易混知识点，采用{method}形成个人笔记。\n"
        "\n"
        "二、病例/题型训练记录\n"
        "- 完成病例题或主观题结构化作答训练。\n"
        "- 对审题、鉴别诊断、结论表达进行二次修订。\n"
        "\n"
        "三、下一步计划\n"
        "- 继续按章节滚动复盘，提升稳定正确率。\n"
        "- 针对薄弱点补做专项训练并跟踪改进。\n"
    )
    file_path.write_text(file_text, encoding="utf-8")
    return f"homework/{filename}"


def build_checkin_content(student, day_offset):
    focus_course = student["focus_course"]
    task_seed = (student["user_id"] + day_offset) % 3
    task = COURSE_HOMEWORK_TASKS.get(focus_course, ["完成章节复盘"])[task_seed]
    progress = CHECKIN_PROGRESS_SNIPPETS[(student["user_id"] + day_offset) % len(CHECKIN_PROGRESS_SNIPPETS)]
    return (
        f"今日学习：{task}。"
        f"同步完成英语阅读与政治选择题巩固。{progress}"
    )


def build_student_profiles():
    students = []
    for idx, (name, gender) in enumerate(STUDENT_NAME_POOL):
        focus_course = PROFESSIONAL_COURSES[idx % len(PROFESSIONAL_COURSES)]
        students.append(
            {
                "username": name,
                "name": name,
                "gender": gender,
                "age": 22 + (idx % 5),
                "major": MAJOR_BY_COURSE[focus_course],
                "grade": f"{2021 + (idx % 4)}级",
                "class": CLASS_BY_COURSE[focus_course],
                "focus_course": focus_course,
            }
        )
    return students

COURSES = [
    {
        "course": "西医临床",
        "teacher_username": "李明",
        "teacher_name": "李明",
        "exam_questions": [
            {"question_type": "single", "content": "高血压患者常用的一线降压药物是？", "options": ["A. 氨氯地平", "B. 维生素C", "C. 葡萄糖", "D. 阿莫西林"], "correct_answer": "A. 氨氯地平", "analysis": "氨氯地平属于钙离子通道阻滞剂，是常见的一线降压药。", "score": 5},
            {"question_type": "single", "content": "成人心肺复苏时，胸外按压频率应为？", "options": ["A. 40-60次/分", "B. 60-80次/分", "C. 100-120次/分", "D. 130-150次/分"], "correct_answer": "C. 100-120次/分", "analysis": "按压频率过慢或过快都会影响复苏效果，指南推荐 100-120 次/分。", "score": 5},
            {"question_type": "judge", "content": "急性心肌梗死患者出现持续胸痛并伴 ST 段抬高时，应尽快启动再灌注治疗。", "correct_answer": "正确", "analysis": "ST 段抬高型心梗需要尽快完成再灌注，以减少心肌坏死范围。", "score": 4},
            {"question_type": "judge", "content": "糖尿病酮症酸中毒的首选补液方式是口服补液。", "correct_answer": "错误", "analysis": "DKA 首选静脉补液并结合胰岛素治疗，口服补液不能满足急救需求。", "score": 4},
            {"question_type": "fill", "content": "慢阻肺急性加重患者吸氧时，血氧饱和度一般控制在 ____ 。", "correct_answer": "88%-92%", "analysis": "慢阻肺患者氧疗目标通常为 88%-92%，以避免二氧化碳潴留加重。", "score": 6},
            {"question_type": "fill", "content": "上消化道出血患者明确病因的首选检查通常是 ____ 。", "correct_answer": "胃镜", "analysis": "胃镜可直接观察出血部位并进行止血处理，是首选检查。", "score": 6},
        ],
    },
    {
        "course": "中医临床",
        "teacher_username": "周凯",
        "teacher_name": "周凯",
        "exam_questions": [
            {"question_type": "single", "content": "中医四诊中不包括以下哪一项？", "options": ["A. 望诊", "B. 闻诊", "C. 问诊", "D. 透析"], "correct_answer": "D. 透析", "analysis": "四诊为望闻问切，透析不属于中医四诊内容。", "score": 5},
            {"question_type": "single", "content": "下列哪项属于八纲辨证内容？", "options": ["A. 表里", "B. 升降", "C. 津液", "D. 三焦"], "correct_answer": "A. 表里", "analysis": "八纲辨证包括阴阳、表里、寒热、虚实。", "score": 5},
            {"question_type": "judge", "content": "舌质淡白多提示气血不足或阳虚。", "correct_answer": "正确", "analysis": "舌质淡白常与气血不足、阳虚、寒证相关。", "score": 4},
            {"question_type": "judge", "content": "切诊只用于观察呼吸频率，与脉象无关。", "correct_answer": "错误", "analysis": "切诊的重要内容之一就是切脉，用于辨别病机。", "score": 4},
            {"question_type": "fill", "content": "中医辨证的核心思维是 ____ 论治。", "correct_answer": "辨证", "analysis": "中医强调辨证论治，根据证候决定治法与方药。", "score": 6},
            {"question_type": "fill", "content": "望诊中观察舌苔厚薄，重点反映病邪的 ____ 情况。", "correct_answer": "深浅", "analysis": "舌苔变化可反映病邪深浅及胃气盛衰。", "score": 6},
        ],
    },
    {
        "course": "口腔医学",
        "teacher_username": "陈洁",
        "teacher_name": "陈洁",
        "exam_questions": [
            {"question_type": "single", "content": "龋病最常见的高危因素是？", "options": ["A. 糖摄入频繁", "B. 缺乏睡眠", "C. 饮水过多", "D. 运动不足"], "correct_answer": "A. 糖摄入频繁", "analysis": "频繁摄入糖类会促进菌斑产酸，是龋病的重要危险因素。", "score": 5},
            {"question_type": "single", "content": "牙周炎早期最常见的临床表现是？", "options": ["A. 牙齿自发脱落", "B. 牙龈出血", "C. 面部麻木", "D. 颞下颌关节弹响"], "correct_answer": "B. 牙龈出血", "analysis": "刷牙或探诊出血是牙周疾病最常见的早期表现。", "score": 5},
            {"question_type": "judge", "content": "乳牙出现龋坏也需要及时治疗。", "correct_answer": "正确", "analysis": "乳牙龋坏会影响恒牙萌出及咀嚼功能，不能忽视。", "score": 4},
            {"question_type": "judge", "content": "所有阻生智齿都不需要处理。", "correct_answer": "错误", "analysis": "若阻生智齿反复冠周炎或影响邻牙，应考虑拔除。", "score": 4},
            {"question_type": "fill", "content": "预防窝沟龋常用的局部措施是窝沟 ____ 。", "correct_answer": "封闭", "analysis": "窝沟封闭可阻断食物残渣与细菌滞留，是常用防龋措施。", "score": 6},
            {"question_type": "fill", "content": "牙周基础治疗中常见的洁治方式包括龈上洁治和 ____ 。", "correct_answer": "龈下刮治", "analysis": "龈下刮治有助于去除牙周袋内菌斑和牙石。", "score": 6},
        ],
    },
    {
        "course": "其他类（护理学、医学技术、基础医学、公共卫生等）",
        "teacher_username": "刘颖",
        "teacher_name": "刘颖",
        "exam_questions": [
            {"question_type": "single", "content": "护理评估的首要环节是？", "options": ["A. 收集资料", "B. 立即给药", "C. 手术操作", "D. 出院宣教"], "correct_answer": "A. 收集资料", "analysis": "护理程序第一步是评估，核心是系统收集资料。", "score": 5},
            {"question_type": "single", "content": "公共卫生工作强调的核心理念是？", "options": ["A. 个体突击治疗", "B. 群体预防", "C. 单科操作", "D. 单次干预"], "correct_answer": "B. 群体预防", "analysis": "公共卫生更重视群体健康促进和疾病预防。", "score": 5},
            {"question_type": "judge", "content": "无菌技术操作中，已污染物品不得再视为无菌。", "correct_answer": "正确", "analysis": "一旦污染即丧失无菌状态，必须重新更换。", "score": 4},
            {"question_type": "judge", "content": "流行病学调查只适用于传染病，不适用于慢性病。", "correct_answer": "错误", "analysis": "流行病学既研究传染病，也研究慢性病等多种健康问题。", "score": 4},
            {"question_type": "fill", "content": "医学统计中，反映一组数据集中趋势的常用指标之一是 ____ 。", "correct_answer": "均数", "analysis": "均数、中位数、众数都是常见的集中趋势指标。", "score": 6},
            {"question_type": "fill", "content": "护理程序通常包括评估、诊断、计划、实施和 ____ 五个环节。", "correct_answer": "评价", "analysis": "评价是护理程序闭环管理的最后一环。", "score": 6},
        ],
    },
    {
        "course": "政治",
        "teacher_username": "王雪",
        "teacher_name": "王雪",
        "exam_questions": [
            {"question_type": "single", "content": "马克思主义中国化时代化的最新理论成果是？", "options": ["A. 毛泽东思想", "B. 邓小平理论", "C. 习近平新时代中国特色社会主义思想", "D. 三个代表重要思想"], "correct_answer": "C. 习近平新时代中国特色社会主义思想", "analysis": "这是当代中国马克思主义、二十一世纪马克思主义。", "score": 5},
            {"question_type": "single", "content": "新发展理念不包括以下哪一项？", "options": ["A. 创新", "B. 协调", "C. 竞争", "D. 共享"], "correct_answer": "C. 竞争", "analysis": "新发展理念包括创新、协调、绿色、开放、共享。", "score": 5},
            {"question_type": "judge", "content": "人民民主专政是我国的国体。", "correct_answer": "正确", "analysis": "人民民主专政是我国宪法规定的国家性质。", "score": 4},
            {"question_type": "judge", "content": "生产关系决定生产力的发展水平，生产力对生产关系没有反作用。", "correct_answer": "错误", "analysis": "应为生产力决定生产关系，生产关系反作用于生产力。", "score": 4},
            {"question_type": "fill", "content": "中国特色社会主义最本质的特征是中国共产党 ____ 。", "correct_answer": "领导", "analysis": "党的领导是中国特色社会主义最本质特征。", "score": 6},
            {"question_type": "fill", "content": "社会主义核心价值观国家层面的内容包括富强、民主、文明、____ 。", "correct_answer": "和谐", "analysis": "国家层面四项为富强、民主、文明、和谐。", "score": 6},
        ],
    },
    {
        "course": "英语",
        "teacher_username": "赵宁",
        "teacher_name": "赵宁",
        "exam_questions": [
            {"question_type": "single", "content": "考研英语阅读理解中，解答主旨题首先应关注？", "options": ["A. 首段和尾段", "B. 单个生词", "C. 标点符号", "D. 手写速度"], "correct_answer": "A. 首段和尾段", "analysis": "主旨题应优先把握文章中心，常结合首尾段与主题句判断。", "score": 5},
            {"question_type": "single", "content": "分析长难句时最先应做的是？", "options": ["A. 背诵全文", "B. 找句子主干", "C. 忽略从句", "D. 直接翻译生词"], "correct_answer": "B. 找句子主干", "analysis": "先找主谓宾主干，再分析从句和修饰成分更高效。", "score": 5},
            {"question_type": "judge", "content": "考研英语一作文部分只考应用文，不考图画作文。", "correct_answer": "错误", "analysis": "英语一通常包括应用文和图画作文两部分。", "score": 4},
            {"question_type": "judge", "content": "阅读理解解题时，识别转折和因果关系有助于定位答案。", "correct_answer": "正确", "analysis": "转折、因果、让步等逻辑关系常是命题重点。", "score": 4},
            {"question_type": "fill", "content": "完形填空作答时，除了词义辨析，还应重点关注上下文 ____ 。", "correct_answer": "逻辑", "analysis": "完形填空非常强调篇章逻辑和语义衔接。", "score": 6},
            {"question_type": "fill", "content": "翻译长难句时，第一步通常是找出句子的 ____ 。", "correct_answer": "主干", "analysis": "抓主干是长难句翻译和语法分析的基本步骤。", "score": 6},
        ],
    },
]


def purge_all_business_data():
    # 先删依赖表，再删主表
    execute("DELETE FROM notification_read")
    execute("DELETE FROM answer")
    execute("DELETE FROM exam_record")
    execute("DELETE FROM question")
    execute("DELETE FROM exam")

    execute("DELETE FROM plan_progress")
    execute("DELETE FROM learning_task")
    execute("DELETE FROM learning_plan")

    execute("DELETE FROM homework_submission")
    execute("DELETE FROM evaluation")
    execute("DELETE FROM checkin")
    execute("DELETE FROM materials")
    execute("DELETE FROM homework")
    execute("DELETE FROM student_info")

    execute("DELETE FROM notification")

    execute("DELETE FROM users")
    execute("DELETE FROM admin_users")


def create_user(username, role):
    return insert_and_get_id(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, USER_PASSWORD_HASH, role),
    )


def seed_base_accounts():
    teacher_ids = {}
    for item in COURSES:
        teacher_ids[item["course"]] = create_user(item["teacher_username"], "teacher")

    student_profiles = build_student_profiles()
    student_rows = []
    for profile in student_profiles:
        student_id = create_user(profile["username"], "student")
        primary_teacher_id = teacher_ids[profile["focus_course"]]
        insert_and_get_id(
            """
            INSERT INTO student_info (user_id, name, gender, age, major, grade, `class`, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                student_id,
                profile["name"],
                profile["gender"],
                profile["age"],
                profile["major"],
                profile["grade"],
                profile["class"],
                primary_teacher_id,
            ),
        )
        student_rows.append(
            {
                **profile,
                "user_id": student_id,
                "teacher_id": primary_teacher_id,
                "exam_subjects": {"政治", "英语", profile["focus_course"]},
            }
        )

    supervisor_id = create_user(SUPERVISOR["username"], "supervisor")

    admin_id = insert_and_get_id(
        "INSERT INTO admin_users (username, password) VALUES (%s, %s)",
        (ADMIN["username"], ADMIN_PASSWORD_HASH),
    )

    return teacher_ids, student_rows, supervisor_id, admin_id


def get_students_for_course(student_rows, course):
    if course in ["政治", "英语"]:
        return list(student_rows)
    return [item for item in student_rows if item["focus_course"] == course]


def seed_course_data(teacher_ids, student_rows):
    now = datetime.now()
    created = {
        "homework": 0,
        "materials": 0,
        "evaluation": 0,
        "homework_submission": 0,
        "exam": 0,
        "question": 0,
        "exam_record": 0,
        "answer": 0,
        "notification": 0,
    }

    homework_items = []

    for idx, item in enumerate(COURSES, start=1):
        teacher_id = teacher_ids[item["course"]]
        relevant_students = get_students_for_course(student_rows, item["course"])

        for hw_no in range(1, 3):
            publish_time = (now - timedelta(days=10 - idx + hw_no)).strftime("%Y-%m-%d %H:%M:%S")
            deadline = (now + timedelta(days=5 + idx + hw_no)).strftime("%Y-%m-%d %H:%M:%S")
            hw_title = f"{item['course']}课程作业{hw_no}"
            hw_content = build_homework_content(item["course"], hw_no)
            homework_id = insert_and_get_id(
                """
                INSERT INTO homework (teacher_id, title, content, publish_time, deadline)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    teacher_id,
                    hw_title,
                    hw_content,
                    publish_time,
                    deadline,
                ),
            )
            created["homework"] += 1
            homework_items.append((homework_id, item["course"], hw_no, hw_title, hw_content))

        for material_no in range(1, 3):
            insert_and_get_id(
                """
                INSERT INTO materials (teacher_id, title, file_path, upload_time, download_count)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    teacher_id,
                    build_material_title(item["course"], material_no),
                    f"materials/course_{idx}_{material_no}.pdf",
                    (now - timedelta(days=8 - material_no)).strftime("%Y-%m-%d %H:%M:%S"),
                    RNG.randint(0, 6),
                ),
            )
            created["materials"] += 1

        for student in relevant_students:
            if RNG.random() < 0.7:
                insert_and_get_id(
                    """
                    INSERT INTO evaluation (student_id, teacher_id, score, content, create_time)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        student["user_id"],
                        teacher_id,
                        RNG.choice([4, 4, 5, 5, 5]),
                        f"{item['course']}课程讲解条理清晰，练习节奏合理。",
                        (now - timedelta(days=RNG.randint(1, 12))).strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                created["evaluation"] += 1

        exam_questions = item["exam_questions"]

        exam_title, exam_desc = build_exam_title_and_description(item["course"], exam_questions, idx, now)

        exam_id = insert_and_get_id(
            """
            INSERT INTO exam (teacher_id, title, description, start_time, end_time, duration_minutes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                teacher_id,
            exam_title,
            exam_desc,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                50,
                "published",
            ),
        )
        created["exam"] += 1

        inserted_questions = []
        for sort_no, question in enumerate(exam_questions, start=1):
            question_id = insert_and_get_id(
                """
                INSERT INTO question (exam_id, question_type, content, options_json, correct_answer, analysis, score, sort_no)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    exam_id,
                    question["question_type"],
                    question["content"],
                    json.dumps(question.get("options"), ensure_ascii=False) if question.get("options") else None,
                    question["correct_answer"],
                    question["analysis"],
                    question["score"],
                    sort_no,
                ),
            )
            inserted_questions.append({**question, "id": question_id})
            created["question"] += 1

        for student in relevant_students:
            if RNG.random() >= 0.65:
                continue
            total_score = 0
            exam_record_id = insert_and_get_id(
                """
                INSERT INTO exam_record (exam_id, student_id, auto_score, manual_score, total_score, status, submit_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    exam_id,
                    student["user_id"],
                    0,
                    0,
                    0,
                    "submitted",
                    (now - timedelta(days=RNG.randint(0, 6))).strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created["exam_record"] += 1

            for question in inserted_questions:
                is_correct = 1 if RNG.random() < 0.82 else 0
                score_awarded = float(question["score"]) if is_correct else 0.0
                total_score += score_awarded
                insert_and_get_id(
                    """
                    INSERT INTO answer (record_id, question_id, answer_text, is_correct, score_awarded)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        exam_record_id,
                        question["id"],
                        question["correct_answer"] if is_correct else "待改进",
                        is_correct,
                        score_awarded,
                    ),
                )
                created["answer"] += 1

            execute(
                "UPDATE exam_record SET auto_score=%s, total_score=%s WHERE id=%s",
                (round(total_score, 2), round(total_score, 2), exam_record_id),
            )

            if RNG.random() < 0.55:
                insert_and_get_id(
                    """
                    INSERT INTO notification (audience_kind, target_user_id, category, level, title, content, action_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        "user",
                        student["user_id"],
                        "exam",
                        "warning",
                        f"{item['course']}考试提醒",
                        f"{item['course']}课程测验已发布，请在规定时间内完成。",
                        "/app/student/exam",
                    ),
                )
                created["notification"] += 1

    for idx, (homework_id, course, hw_no, hw_title, hw_content) in enumerate(homework_items, start=1):
        relevant_students = get_students_for_course(student_rows, course)
        for student in relevant_students:
            if RNG.random() >= 0.68:
                continue
            score = RNG.randint(74, 96)
            submission_file_path = write_submission_attachment(
                course=course,
                student_name=student["name"],
                hw_no=hw_no,
                homework_id=homework_id,
                student_id=student["user_id"],
                homework_title=hw_title,
                homework_content=hw_content,
            )
            insert_and_get_id(
                """
                INSERT INTO homework_submission (homework_id, student_id, content, file_path, score, feedback, submit_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    homework_id,
                    student["user_id"],
                    build_submission_content(
                        course,
                        student["name"],
                        hw_no,
                        hw_title,
                        hw_content,
                        int(student["user_id"]),
                    ),
                    submission_file_path,
                    score,
                    "结构完整，建议继续强化高频易错点。" if score < 85 else "完成较好，继续保持节奏。",
                    (now - timedelta(days=RNG.randint(0, 5))).strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created["homework_submission"] += 1

    return created


def seed_student_growth_data(student_rows):
    now = datetime.now()
    created = {
        "checkin": 0,
        "learning_plan": 0,
        "learning_task": 0,
        "plan_progress": 0,
        "notification": 0,
    }

    for student in student_rows:
        checkin_days = RNG.randint(6, 10)
        offsets = sorted(RNG.sample(range(1, 15), checkin_days))
        for day_offset in offsets:
            checkin_day = now - timedelta(days=day_offset)
            insert_and_get_id(
                """
                INSERT INTO checkin (student_id, content, file_path, checkin_date, create_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    student["user_id"],
                    build_checkin_content(student, day_offset),
                    f"checkin/student_{student['user_id']}_{day_offset}.png",
                    checkin_day.strftime("%Y-%m-%d"),
                    checkin_day.replace(hour=21, minute=RNG.randint(0, 45), second=0).strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            created["checkin"] += 1

        learning_plan_id = insert_and_get_id(
            """
            INSERT INTO learning_plan (student_id, title, target, start_date, end_date, remind_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                student["user_id"],
                f"{student['name']}考研阶段学习计划",
                f"聚焦政治、英语与{student['focus_course']}专业课提分。",
                (now - timedelta(days=14)).strftime("%Y-%m-%d"),
                (now + timedelta(days=28)).strftime("%Y-%m-%d"),
                "20:30:00",
                "ongoing",
            ),
        )
        created["learning_plan"] += 1

        subjects = ["政治", "英语", student["focus_course"]]
        task_index = 0
        for subject in subjects:
            for round_no in [1, 2]:
                task_index += 1
                is_done = 1 if task_index <= 3 else 0
                insert_and_get_id(
                    """
                    INSERT INTO learning_task (plan_id, task_title, task_date, estimated_minutes, sort_no, is_done)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        learning_plan_id,
                        build_learning_task_title(subject, round_no),
                        (now - timedelta(days=12 - task_index)).strftime("%Y-%m-%d"),
                        RNG.choice([70, 80, 90, 100]),
                        task_index,
                        is_done,
                    ),
                )
                created["learning_task"] += 1

        for day_offset in [9, 6, 3, 1]:
            progress_day = now - timedelta(days=day_offset)
            insert_and_get_id(
                """
                INSERT INTO plan_progress (plan_id, progress_date, study_minutes, note)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    learning_plan_id,
                    progress_day.strftime("%Y-%m-%d"),
                    RNG.randint(70, 150),
                    f"{student['focus_course']}阶段复盘与错题整理。",
                ),
            )
            created["plan_progress"] += 1

        for category, path in [("homework", "/app/student/homework"), ("materials", "/app/student/materials")]:
            insert_and_get_id(
                """
                INSERT INTO notification (audience_kind, target_user_id, category, level, title, content, action_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "user",
                    student["user_id"],
                    category,
                    "info",
                    f"{category}更新提醒",
                    f"{student['focus_course']}学习相关{category}已更新，请及时查看。",
                    path,
                ),
            )
            created["notification"] += 1

    return created


def seed_admin_notification(admin_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notification_id = insert_and_get_id(
        """
        INSERT INTO notification (audience_kind, target_admin_id, category, level, title, content, action_path, create_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "admin",
            admin_id,
            "system",
            "warning",
            "测试数据重置完成",
            "系统已按医学考研六类课程重建扩展测试数据（含多学员、多作业、多打卡与学习进度）。",
            "/admin/notifications",
            now,
        ),
    )
    return notification_id


def summary_counts():
    return {
        "users": query_one("SELECT COUNT(*) AS c FROM users")["c"],
        "admin_users": query_one("SELECT COUNT(*) AS c FROM admin_users")["c"],
        "student_info": query_one("SELECT COUNT(*) AS c FROM student_info")["c"],
        "homework": query_one("SELECT COUNT(*) AS c FROM homework")["c"],
        "materials": query_one("SELECT COUNT(*) AS c FROM materials")["c"],
        "checkin": query_one("SELECT COUNT(*) AS c FROM checkin")["c"],
        "evaluation": query_one("SELECT COUNT(*) AS c FROM evaluation")["c"],
        "homework_submission": query_one("SELECT COUNT(*) AS c FROM homework_submission")["c"],
        "learning_plan": query_one("SELECT COUNT(*) AS c FROM learning_plan")["c"],
        "learning_task": query_one("SELECT COUNT(*) AS c FROM learning_task")["c"],
        "plan_progress": query_one("SELECT COUNT(*) AS c FROM plan_progress")["c"],
        "exam": query_one("SELECT COUNT(*) AS c FROM exam")["c"],
        "question": query_one("SELECT COUNT(*) AS c FROM question")["c"],
        "exam_record": query_one("SELECT COUNT(*) AS c FROM exam_record")["c"],
        "answer": query_one("SELECT COUNT(*) AS c FROM answer")["c"],
        "notification": query_one("SELECT COUNT(*) AS c FROM notification")["c"],
        "notification_read": query_one("SELECT COUNT(*) AS c FROM notification_read")["c"],
    }


def main():
    purge_all_business_data()
    teacher_ids, student_rows, supervisor_id, admin_id = seed_base_accounts()
    per_course_created = seed_course_data(teacher_ids, student_rows)
    growth_created = seed_student_growth_data(student_rows)
    admin_notice_id = seed_admin_notification(admin_id)

    print("已删除其他历史数据，并完成医学考研六类课程测试数据重建。")
    print(
        {
            "login_accounts": {
                "students_sample": [{"username": item["username"], "password": USER_PASSWORD} for item in student_rows[:6]],
                "student_total": len(student_rows),
                "supervisor": {"username": SUPERVISOR["username"], "password": USER_PASSWORD},
                "admin": {"username": ADMIN["username"], "password": ADMIN_PASSWORD},
                "teachers": [{"course": c["course"], "username": c["teacher_username"], "password": USER_PASSWORD} for c in COURSES],
            },
            "per_course_created": per_course_created,
            "student_growth_created": growth_created,
            "admin_notification_id": admin_notice_id,
            "total_counts": summary_counts(),
        }
    )


if __name__ == "__main__":
    main()
