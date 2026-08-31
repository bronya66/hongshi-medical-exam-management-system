from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import query_all, execute


def main():
    target_dir = BACKEND_DIR / "uploads" / "homework"
    target_dir.mkdir(parents=True, exist_ok=True)

    rows = query_all(
        """
        SELECT
            hs.id,
            hs.homework_id,
            hs.student_id,
            hs.content,
            IFNULL(si.name, u.username) AS student_name,
            h.title AS homework_title,
            h.content AS homework_content
        FROM homework_submission hs
        LEFT JOIN student_info si ON si.user_id = hs.student_id
        LEFT JOIN users u ON u.id = hs.student_id
        LEFT JOIN homework h ON h.id = hs.homework_id
        ORDER BY hs.id ASC
        """
    )

    updated = 0
    for row in rows:
        filename = f"submission_real_{int(row['id'])}.txt"
        abs_path = target_dir / filename

        sid = int(row["student_id"] or 0)
        rid = int(row["id"])
        style = ["限时作答", "错因复盘", "结构化套写"][rid % 3]
        weak = ["关键词覆盖", "鉴别诊断逻辑", "知识点边界", "审题准确率"][sid % 4]
        requirement = (str(row.get("homework_content") or "").split("\n")[0] or "完成作业训练").strip()
        personalized_content = (
            f"围绕《{row.get('homework_title') or '阶段作业'}》完成提交；"
            f"按“{requirement}”执行，采用{style}方式推进，重点修正{weak}。"
        )

        text = (
            f"学员：{row.get('student_name') or ''}\n"
            f"作业：{row.get('homework_title') or ''}\n"
            f"提交ID：{row['id']}\n"
            "\n"
            "作业要求：\n"
            f"{row.get('homework_content') or ''}\n"
            "\n"
            "提交内容：\n"
            f"{row.get('content') or ''}\n"
            f"本次按“{requirement}”完成任务，采用{style}方式推进。\n"
            "\n"
            "复盘记录：\n"
            "1. 已完成章节高频考点梳理。\n"
            f"2. 已整理错题并标注错因，重点修正{weak}。\n"
            f"3. 下一步继续按{style}节奏强化薄弱项。\n"
        )
        abs_path.write_text(text, encoding="utf-8")

        execute(
            "UPDATE homework_submission SET content=%s, file_path=%s WHERE id=%s",
            (personalized_content, f"homework/{filename}", int(row["id"])),
        )
        updated += 1

    print({"total_candidates": len(rows), "updated": updated})


if __name__ == "__main__":
    main()
