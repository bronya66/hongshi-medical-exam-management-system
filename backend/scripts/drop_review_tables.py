import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, query_one


TABLES = ["review_record", "review_task", "review_plan"]


def table_exists(table_name):
    row = query_one(
        """
        SELECT COUNT(*) AS c
        FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = %s
        """,
        (table_name,),
    )
    return int((row or {}).get("c") or 0) > 0


def main():
    before = {name: table_exists(name) for name in TABLES}

    # 按外键依赖顺序删除
    for table_name in TABLES:
        execute(f"DROP TABLE IF EXISTS {table_name}")

    after = {name: table_exists(name) for name in TABLES}

    print(
        {
            "dropped_tables": TABLES,
            "exists_before": before,
            "exists_after": after,
        }
    )


if __name__ == "__main__":
    main()
