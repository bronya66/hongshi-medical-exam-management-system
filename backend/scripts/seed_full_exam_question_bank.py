import json
import random
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, insert_and_get_id, query_all


# 说明：
# 1) 本脚本生成“原创高质量模拟题（依据公开考研大纲）”，不直接复制真题原文。
# 2) 运行后会清理本脚本覆盖的课程章节题库，再按要求重建。
# 3) 题型分值与系统现有规则保持一致。

SOURCE = "高质量原创模拟题（依据公开考研大纲）"
SCORE_MAP = {
    "single": 5,
    "multi": 2,
    "pair": 2,
    "judge": 4,
    "fill": 6,
    "term": 8,
    "short": 10,
    "essay": 12,
}

COURSE_PLAN = {
    "西医临床": [
        {"section_no": 1, "section_title": "循环系统基础", "counts": {"single": 20, "multi": 8, "pair": 8}},
        {"section_no": 2, "section_title": "呼吸与消化系统", "counts": {"single": 20, "multi": 8, "pair": 8}},
        {"section_no": 3, "section_title": "内分泌与代谢疾病", "counts": {"single": 15, "multi": 6, "pair": 6}},
        {"section_no": 4, "section_title": "血液系统疾病", "counts": {"single": 15, "multi": 6, "pair": 6}},
        {"section_no": 5, "section_title": "泌尿系统疾病", "counts": {"single": 15, "multi": 6, "pair": 6}},
    ],
    "中医临床": [
        {"section_no": 1, "section_title": "四诊与八纲辨证", "counts": {"single": 18, "multi": 6, "pair": 6}},
        {"section_no": 2, "section_title": "治法与脏腑辨证", "counts": {"single": 18, "multi": 6, "pair": 6}},
        {"section_no": 3, "section_title": "中药学与方剂学", "counts": {"single": 15, "multi": 5, "pair": 5}},
        {"section_no": 4, "section_title": "中医内科学", "counts": {"single": 20, "multi": 8, "pair": 8}},
    ],
    "口腔医学": [
        {"section_no": 1, "section_title": "龋病与牙体牙髓", "counts": {"single": 15, "multi": 6, "term": 4, "short": 4, "essay": 4}},
        {"section_no": 2, "section_title": "牙周与口腔预防", "counts": {"single": 15, "multi": 6, "term": 4, "short": 4, "essay": 4}},
        {"section_no": 3, "section_title": "口腔颌面外科学", "counts": {"single": 12, "multi": 5, "term": 3, "short": 3, "essay": 3}},
    ],
    "其他类（护理学、医学技术、基础医学、公共卫生等）": [
        {"section_no": 1, "section_title": "护理程序与基础操作", "counts": {"single": 12, "multi": 5, "term": 3, "short": 3, "essay": 3}},
        {"section_no": 2, "section_title": "公共卫生与医学统计", "counts": {"single": 12, "multi": 5, "term": 3, "short": 3, "essay": 3}},
        {"section_no": 3, "section_title": "基础医学（解剖、生理、生化）", "counts": {"single": 15, "multi": 6, "term": 4, "short": 4, "essay": 4}},
    ],
    "政治": [
        {"section_no": 1, "section_title": "马克思主义基本原理", "counts": {"single": 20, "multi": 12, "short": 8}},
        {"section_no": 2, "section_title": "中国特色社会主义理论", "counts": {"single": 20, "multi": 12, "short": 8}},
        {"section_no": 3, "section_title": "中国近现代史纲要", "counts": {"single": 15, "multi": 10, "short": 6}},
        {"section_no": 4, "section_title": "思想道德修养与法律基础", "counts": {"single": 15, "multi": 10, "short": 6}},
    ],
    "英语": [
        {"section_no": 1, "section_title": "阅读理解", "counts": {"single": 25, "fill": 5, "short": 5}},
        {"section_no": 2, "section_title": "完形与翻译", "counts": {"single": 20, "fill": 8, "short": 8}},
        {"section_no": 3, "section_title": "词汇与语法", "counts": {"single": 15, "fill": 5, "short": 5}},
    ],
}

KNOWLEDGE_POOL = {
    "西医临床": {
        1: ["心力衰竭分级", "急性冠脉综合征", "高血压分层", "心律失常识别", "心源性休克", "抗血小板治疗", "血流动力学评估", "心电图判读"],
        2: ["慢阻肺急性加重", "社区获得性肺炎", "上消化道出血", "急性胰腺炎", "肝硬化并发症", "胃食管反流病", "呼吸衰竭分型", "内镜止血策略"],
        3: ["糖尿病酮症酸中毒", "甲状腺功能异常", "肾上腺疾病", "代谢综合征", "低血糖处理", "胰岛素治疗", "垂体病变", "电解质紊乱"],
        4: ["缺铁性贫血", "巨幼细胞贫血", "再生障碍性贫血", "白血病分型", "血小板减少", "凝血功能障碍", "淋巴瘤评估", "输血指征"],
        5: ["急性肾损伤", "慢性肾脏病分期", "肾小球肾炎", "肾病综合征", "酸碱平衡", "水钠代谢", "透析适应证", "肾性高血压"],
    },
    "中医临床": {
        1: ["望闻问切", "阴阳辨证", "寒热辨证", "虚实辨证", "表里辨证", "气血津液", "舌象分析", "脉象判别"],
        2: ["治病求本", "扶正祛邪", "汗吐下和温清补消", "脏腑辨证", "气血辨证", "六经辨证", "卫气营血辨证", "三焦辨证"],
        3: ["四气五味", "升降浮沉", "归经理论", "配伍禁忌", "君臣佐使", "方剂组成", "经典方证", "加减化裁"],
        4: ["咳嗽辨证论治", "胸痹心痛", "胃脘痛", "眩晕", "不寐", "郁证", "痹证", "水肿"],
    },
    "口腔医学": {
        1: ["龋病病因学", "牙体缺损修复", "牙髓炎鉴别", "根尖周病", "根管治疗步骤", "活力测试", "窝沟封闭", "牙体预备"],
        2: ["牙周炎分级", "菌斑控制", "龈下刮治", "牙周维护", "口腔健康教育", "阻生齿冠周炎", "洁治流程", "风险评估"],
        3: ["下颌阻生牙", "颌面间隙感染", "颌骨骨折", "唇腭裂评估", "口腔颌面肿瘤", "麻醉并发症", "术后感染预防", "创伤处置"],
    },
    "其他类（护理学、医学技术、基础医学、公共卫生等）": {
        1: ["护理评估", "护理诊断", "护理计划", "无菌技术", "静脉输液", "病情观察", "跌倒风险", "护理记录"],
        2: ["发病率与患病率", "筛检试验", "假设检验", "置信区间", "队列研究", "病例对照研究", "健康促进", "公共卫生干预"],
        3: ["人体解剖标志", "神经系统传导", "循环生理", "呼吸调节", "糖脂代谢", "酸碱平衡", "细胞信号转导", "酶学基础"],
    },
    "政治": {
        1: ["实践与认识", "矛盾普遍性与特殊性", "社会存在与社会意识", "历史唯物主义", "价值规律", "人民群众观点", "真理观", "联系与发展"],
        2: ["新发展理念", "中国式现代化", "高质量发展", "共同富裕", "全面依法治国", "总体国家安全观", "党的建设", "全过程人民民主"],
        3: ["新民主主义革命", "社会主义改造", "改革开放", "民族复兴历程", "抗战史实", "党史重要节点", "新中国建设", "现代化进程"],
        4: ["理想信念", "社会主义核心价值观", "法治思维", "宪法精神", "公民道德", "社会公德", "职业道德", "网络法治"],
    },
    "英语": {
        1: ["主旨题", "细节题", "推理题", "词义猜测", "作者态度", "标题匹配", "段落结构", "信息定位"],
        2: ["完形逻辑", "语篇衔接", "英汉翻译", "长难句拆分", "从句分析", "句法转换", "语义重构", "翻译策略"],
        3: ["高频词义辨析", "固定搭配", "时态语态", "非谓语动词", "虚拟语气", "名词性从句", "定语从句", "连词逻辑"],
    },
}


def letter_options(raw_options):
    letters = ["A", "B", "C", "D", "E"]
    return [f"{letters[i]}. {raw_options[i]}" for i in range(len(raw_options))]


def calc_difficulty(index, total):
    if total <= 0:
        return "medium"
    ratio = (index + 1) / float(total)
    if ratio <= 0.3:
        return "easy"
    if ratio <= 0.8:
        return "medium"
    return "hard"


def base_topic(course, section_no, idx):
    topic_list = KNOWLEDGE_POOL.get(course, {}).get(section_no) or ["核心考点"]
    return topic_list[idx % len(topic_list)]


def build_single(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    if course == "英语":
        stem = f"{course}第{section_no}节《{section_title}》单选题{idx + 1}：关于{topic}的解题策略，下列说法正确的是？"
        raw = [
            "先定位题干关键词并回原文验证证据",
            "只按选项长度判断答案",
            "忽略上下文逻辑关系",
            "跳过题干直接看选项",
        ]
        analysis = "英语客观题应坚持“题干定位-证据回文-选项比对”的步骤。"
    elif course == "政治":
        stem = f"{course}第{section_no}节《{section_title}》单选题{idx + 1}：关于{topic}，下列说法正确的是？"
        raw = [
            "应在教材概念框架内结合现实语境理解命题",
            "可完全脱离历史条件作抽象判断",
            "理论命题不需要区分概念边界",
            "只凭个人观点即可判定正误",
        ]
        analysis = "政治客观题强调概念准确和边界清晰，正确项符合教材规范。"
    elif course == "中医临床":
        stem = f"{course}第{section_no}节《{section_title}》单选题{idx + 1}：针对{topic}，下列说法正确的是？"
        raw = [
            "应先辨证分型，再确定治法方药",
            "可不辨证直接套用固定方",
            "仅依据单一症状即可下结论",
            "虚实寒热差异不影响处置",
        ]
        analysis = "中医题核心在辨证论治，正确项体现辨证先行原则。"
    else:
        stem = f"{course}第{section_no}节《{section_title}》单选题{idx + 1}：关于{topic}，下列说法正确的是？"
        raw = [
            "应结合病史、体征和关键检查结果综合判断",
            "可忽略适应证与禁忌证差异",
            "仅凭单一指标即可确定诊疗方案",
            "不需进行风险分层即可直接定论",
        ]
        analysis = "该题考查临床综合判断能力，正确项符合规范诊疗思路。"

    options = letter_options(raw)
    return {
        "question_type": "single",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": stem,
        "options_json": json.dumps(options, ensure_ascii=False),
        "correct_answer": options[0],
        "analysis": analysis,
    }


def build_multi(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    stem = f"{course}第{section_no}节《{section_title}》多选题{idx + 1}：关于{topic}，下列说法正确的是（可多选）？"
    if course == "政治":
        raw = [
            "需把握概念内涵与外延",
            "需结合历史条件与现实语境",
            "可以忽略命题中的限定词",
            "应防范偷换概念类干扰项",
            "只要表述积极就一定正确",
        ]
        analysis = "政治多选常考概念边界与条件限制，A/B/D符合规范。"
    elif course == "英语":
        raw = [
            "先看题干再定位原文证据",
            "注意转折、因果和指代关系",
            "可以不读上下文直接选词",
            "比较选项时关注同义改写",
            "只按语感即可稳定满分",
        ]
        analysis = "英语多选/不定项题需以证据为核心，A/B/D为有效策略。"
    else:
        raw = [
            "应先明确概念边界和判定条件",
            "需结合关键证据链进行推理",
            "可以跳过鉴别诊断步骤",
            "应识别绝对化表述的干扰项",
            "经验记忆可替代规范判断",
        ]
        analysis = "多选题重点在条件判断与证据整合，A/B/D正确。"

    options = letter_options(raw)
    return {
        "question_type": "multi",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": stem,
        "options_json": json.dumps(options, ensure_ascii=False),
        "correct_answer": "A;B;D",
        "analysis": analysis,
    }


def build_pair(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    stem = f"{course}第{section_no}节《{section_title}》配伍题{idx + 1}：将{topic}相关临床/理论场景与最匹配的处理要点进行配对，最佳选项是？"
    raw = [
        "先完成关键评估并明确首要处理目标",
        "仅依据单一表现立即终结判断",
        "忽略病程分期统一处理",
        "跳过适应证与禁忌证核对",
        "将并发症风险评估延后处理",
    ]
    options = letter_options(raw)
    return {
        "question_type": "pair",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": stem,
        "options_json": json.dumps(options, ensure_ascii=False),
        "correct_answer": options[0],
        "analysis": "配伍题考查“情境-策略”对应关系，正确项体现先评估后决策。",
    }


def build_fill(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    stem = f"{course}第{section_no}节《{section_title}》填空题{idx + 1}：围绕{topic}，规范解题中首先要把握的关键词是 ____ 。"
    answer = "核心证据"
    if course == "英语":
        answer = "主干"
    elif course == "政治":
        answer = "概念边界"
    elif course == "中医临床":
        answer = "辨证"
    analysis = "填空题侧重关键术语识记与应用。"
    return {
        "question_type": "fill",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": stem,
        "options_json": None,
        "correct_answer": answer,
        "analysis": analysis,
    }


def build_term(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    return {
        "question_type": "term",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": f"{course}第{section_no}节《{section_title}》名词解释{idx + 1}：请解释“{topic}”并写出核心判定要点。",
        "options_json": None,
        "correct_answer": "定义准确、要点完整、术语规范。",
        "analysis": "名词解释评分看定义准确性、关键特征完整性和表达规范性。",
    }


def build_short(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    return {
        "question_type": "short",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": f"{course}第{section_no}节《{section_title}》简答题{idx + 1}：围绕{topic}，按“核心概念-关键依据-应用场景”作答。",
        "options_json": None,
        "correct_answer": "参考要点：概念准确、逻辑清晰、要点完整。",
        "analysis": "简答题建议分点作答，突出依据与应用。",
    }


def build_essay(course, section_no, section_title, idx, total):
    topic = base_topic(course, section_no, idx)
    return {
        "question_type": "essay",
        "difficulty": calc_difficulty(idx, total),
        "knowledge_point": topic,
        "content": f"{course}第{section_no}节《{section_title}》论述题{idx + 1}：请围绕{topic}进行系统论述，并结合典型情境分析。",
        "options_json": None,
        "correct_answer": "参考要点：概念界定、理论依据、关键流程、常见误区、综合应用。",
        "analysis": "论述题评分关注观点正确性、结构完整性与分析深度。",
    }


def generate_question(course, section_no, section_title, question_type, idx, total):
    if question_type == "single":
        q = build_single(course, section_no, section_title, idx, total)
    elif question_type == "multi":
        q = build_multi(course, section_no, section_title, idx, total)
    elif question_type == "pair":
        q = build_pair(course, section_no, section_title, idx, total)
    elif question_type == "fill":
        q = build_fill(course, section_no, section_title, idx, total)
    elif question_type == "term":
        q = build_term(course, section_no, section_title, idx, total)
    elif question_type == "short":
        q = build_short(course, section_no, section_title, idx, total)
    elif question_type == "essay":
        q = build_essay(course, section_no, section_title, idx, total)
    else:
        raise ValueError(f"Unsupported question_type: {question_type}")

    q["score"] = SCORE_MAP[question_type]
    q["source"] = SOURCE
    return q


def delete_existing_for_plan():
    for course in COURSE_PLAN.keys():
        execute("DELETE FROM question_bank WHERE course=%s", (course,))


def insert_generated_questions():
    inserted = 0
    for course, sections in COURSE_PLAN.items():
        for sec in sections:
            section_no = int(sec["section_no"])
            section_title = sec["section_title"]
            counts = sec["counts"]
            for question_type, total in counts.items():
                for idx in range(int(total)):
                    q = generate_question(course, section_no, section_title, question_type, idx, int(total))
                    insert_and_get_id(
                        """
                        INSERT INTO question_bank (
                            course, section_no, section_title, question_type,
                            difficulty, knowledge_point, content, options_json,
                            correct_answer, analysis, score, source
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            course,
                            section_no,
                            section_title,
                            question_type,
                            q["difficulty"],
                            q["knowledge_point"][:120],
                            q["content"],
                            q["options_json"],
                            q["correct_answer"],
                            q["analysis"],
                            q["score"],
                            q["source"][:120],
                        ),
                    )
                    inserted += 1
    return inserted


def print_verification():
    rows = query_all(
        """
        SELECT course, section_no, section_title,
               SUM(CASE WHEN question_type='single' THEN 1 ELSE 0 END) AS single_count,
               SUM(CASE WHEN question_type='multi' THEN 1 ELSE 0 END) AS multi_count,
               SUM(CASE WHEN question_type='pair' THEN 1 ELSE 0 END) AS pair_count,
               SUM(CASE WHEN question_type='judge' THEN 1 ELSE 0 END) AS judge_count,
               SUM(CASE WHEN question_type='fill' THEN 1 ELSE 0 END) AS fill_count,
               SUM(CASE WHEN question_type='term' THEN 1 ELSE 0 END) AS term_count,
               SUM(CASE WHEN question_type='short' THEN 1 ELSE 0 END) AS short_count,
               SUM(CASE WHEN question_type='essay' THEN 1 ELSE 0 END) AS essay_count,
               COUNT(*) AS total
        FROM question_bank
        WHERE course IN (%s, %s, %s, %s, %s, %s)
        GROUP BY course, section_no, section_title
        ORDER BY course ASC, section_no ASC
        """,
        tuple(COURSE_PLAN.keys()),
    )

    expected_total = 0
    print("\n=== 题库导入校验 ===")
    for course, sections in COURSE_PLAN.items():
        for sec in sections:
            expected_total += sum(int(v) for v in sec["counts"].values())

    print(f"计划总题数: {expected_total}")
    print(f"实际分组数: {len(rows)}")

    for row in rows:
        print(
            f"{row['course']} 第{row['section_no']}节《{row['section_title']}》"
            f" | single={int(row.get('single_count') or 0)}"
            f" multi={int(row.get('multi_count') or 0)}"
            f" pair={int(row.get('pair_count') or 0)}"
            f" fill={int(row.get('fill_count') or 0)}"
            f" term={int(row.get('term_count') or 0)}"
            f" short={int(row.get('short_count') or 0)}"
            f" essay={int(row.get('essay_count') or 0)}"
            f" total={int(row.get('total') or 0)}"
        )


def main():
    random.seed(20260318)
    delete_existing_for_plan()
    inserted = insert_generated_questions()
    print(f"已插入题目数量: {inserted}")
    print_verification()


if __name__ == "__main__":
    main()
