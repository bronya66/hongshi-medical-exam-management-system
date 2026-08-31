import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, insert_and_get_id, query_all


# 本脚本只负责导入“已授权的真实题库文件”，不会自动生成题目。
# 用法示例：
# python scripts/seed_real_exam_questions.py --input scripts/real_exam_questions.json --replace

ALLOWED_TYPES = {"single", "multi", "pair", "judge", "fill", "term", "short", "essay"}
REAL_SOURCE_KEYWORDS = ["真题", "授权", "公开题库", "院校题库"]
DEFAULT_SCORE = {"single": 5, "multi": 2, "pair": 2, "judge": 4, "fill": 6, "term": 8, "short": 10, "essay": 12}

MIN_PLAN = {
    "西医临床": {1: 30, 2: 30, 3: 30, 4: 30, 5: 30},
    "中医临床": {1: 30, 2: 30, 3: 30, 4: 30},
    "口腔医学": {1: 25, 2: 25, 3: 25},
    "其他类（护理学、医学技术、基础医学、公共卫生等）": {1: 25, 2: 25, 3: 25},
    "政治": {1: 35, 2: 35, 3: 35, 4: 35},
    "英语": {1: 35, 2: 35, 3: 35},
}


def is_real_source(text):
    s = str(text or "")
    return any(k in s for k in REAL_SOURCE_KEYWORDS)


def normalize_options(raw):
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("options 必须是数组")
    return json.dumps([str(x).strip() for x in raw], ensure_ascii=False)


def validate_record(item, index):
    required = ["course", "section_no", "section_title", "question_type", "content", "correct_answer", "analysis", "source"]
    for key in required:
        if key not in item or str(item.get(key) or "").strip() == "":
            raise ValueError(f"第{index + 1}条缺少字段: {key}")

    qtype = str(item["question_type"]).strip()
    if qtype not in ALLOWED_TYPES:
        raise ValueError(f"第{index + 1}条 question_type 非法: {qtype}")

    if not is_real_source(item.get("source")):
        raise ValueError(f"第{index + 1}条 source 未标注真实来源关键词（真题/授权/公开题库/院校题库）")

    options = item.get("options")
    if qtype == "single":
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"第{index + 1}条单选题 options 必须为4项")
    elif qtype in ["multi", "pair"]:
        if not isinstance(options, list) or len(options) != 5:
            raise ValueError(f"第{index + 1}条 {qtype} options 必须为5项")

    if qtype == "multi":
        ans = str(item.get("correct_answer") or "")
        picks = [x for x in ans.replace("，", ";").replace(",", ";").split(";") if x.strip()]
        if len(picks) < 2 or len(picks) > 4:
            raise ValueError(f"第{index + 1}条多选题正确答案数量必须为2-4")


def load_input(path):
    content = Path(path).read_text(encoding="utf-8")
    data = json.loads(content)
    if isinstance(data, dict):
        rows = data.get("questions")
    else:
        rows = data
    if not isinstance(rows, list) or not rows:
        raise ValueError("输入文件必须是数组，或包含 questions 数组")
    return rows


def replace_sections(records):
    section_keys = {(str(r["course"]).strip(), int(r["section_no"])) for r in records}
    for course, section_no in section_keys:
        execute("DELETE FROM question_bank WHERE course=%s AND section_no=%s", (course, section_no))


def insert_records(records):
    inserted = 0
    for idx, item in enumerate(records):
        validate_record(item, idx)
        qtype = str(item["question_type"]).strip()
        score = float(item.get("score") or DEFAULT_SCORE[qtype])
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
                str(item["course"]).strip(),
                int(item["section_no"]),
                str(item["section_title"]).strip(),
                qtype,
                str(item.get("difficulty") or "medium"),
                str(item.get("knowledge_point") or item["section_title"])[:120],
                str(item["content"]).strip(),
                normalize_options(item.get("options")),
                str(item["correct_answer"]).strip(),
                str(item["analysis"]).strip(),
                score,
                str(item["source"]).strip()[:120],
            ),
        )
        inserted += 1
    return inserted


def verify_minimums():
    rows = query_all(
        """
        SELECT course, section_no, COUNT(*) AS total
        FROM question_bank
        WHERE source IS NOT NULL
          AND (source LIKE '%%真题%%' OR source LIKE '%%授权%%' OR source LIKE '%%公开题库%%' OR source LIKE '%%院校题库%%')
        GROUP BY course, section_no
        """
    )

    actual = defaultdict(int)
    for row in rows:
        actual[(str(row["course"]), int(row["section_no"]))] = int(row.get("total") or 0)

    failures = []
    for course, sec_map in MIN_PLAN.items():
        for section_no, min_total in sec_map.items():
            have = actual.get((course, section_no), 0)
            if have < min_total:
                failures.append((course, section_no, min_total, have))

    return failures


def print_stats():
    rows = query_all(
        """
        SELECT course, section_no, section_title,
               SUM(CASE WHEN question_type='single' THEN 1 ELSE 0 END) AS single_count,
               SUM(CASE WHEN question_type='multi' THEN 1 ELSE 0 END) AS multi_count,
               SUM(CASE WHEN question_type='pair' THEN 1 ELSE 0 END) AS pair_count,
               SUM(CASE WHEN question_type='fill' THEN 1 ELSE 0 END) AS fill_count,
               SUM(CASE WHEN question_type='term' THEN 1 ELSE 0 END) AS term_count,
               SUM(CASE WHEN question_type='short' THEN 1 ELSE 0 END) AS short_count,
               SUM(CASE WHEN question_type='essay' THEN 1 ELSE 0 END) AS essay_count,
               COUNT(*) AS total
        FROM question_bank
        WHERE source IS NOT NULL
          AND (source LIKE '%%真题%%' OR source LIKE '%%授权%%' OR source LIKE '%%公开题库%%' OR source LIKE '%%院校题库%%')
        GROUP BY course, section_no, section_title
        ORDER BY course ASC, section_no ASC
        """
    )

    print("\n=== 真实题库统计 ===")
    for row in rows:
        print(
            f"{row['course']} 第{row['section_no']}节《{row['section_title']}》"
            f" total={int(row.get('total') or 0)}"
            f" single={int(row.get('single_count') or 0)}"
            f" multi={int(row.get('multi_count') or 0)}"
            f" pair={int(row.get('pair_count') or 0)}"
            f" fill={int(row.get('fill_count') or 0)}"
            f" term={int(row.get('term_count') or 0)}"
            f" short={int(row.get('short_count') or 0)}"
            f" essay={int(row.get('essay_count') or 0)}"
        )


def main():
    parser = argparse.ArgumentParser(description="导入已授权真实考研题目到 question_bank")
    parser.add_argument("--input", required=True, help="真实题库 JSON 文件路径")
    parser.add_argument("--replace", action="store_true", help="按 course+section 覆盖导入")
    args = parser.parse_args()

    records = load_input(args.input)
    if args.replace:
        replace_sections(records)

    inserted = insert_records(records)
    print(f"已导入真实题目数量: {inserted}")

    failures = verify_minimums()
    print_stats()
    if failures:
        print("\n以下章节真实题量未达到最低要求：")
        for item in failures:
            print(f"- {item[0]} 第{item[1]}节：最低{item[2]}，当前{item[3]}")
        raise SystemExit(2)

    print("\n真实题库校验通过。")


if __name__ == "__main__":
    main()
