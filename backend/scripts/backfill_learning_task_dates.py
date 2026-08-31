from datetime import date, datetime, timedelta
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db import execute, query_all


def to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def main():
    plans = query_all("SELECT id, title, start_date FROM learning_plan ORDER BY id ASC")
    total_updated = 0

    for plan in plans:
        tasks = query_all(
            "SELECT id, task_date, sort_no FROM learning_task WHERE plan_id=%s ORDER BY sort_no ASC, id ASC",
            (plan["id"],),
        )
        if not tasks:
            continue

        filled_dates = {}
        last_date = None
        plan_start_date = to_date(plan.get("start_date"))

        for task in tasks:
            current_date = to_date(task.get("task_date"))
            if current_date:
                last_date = current_date
                continue

            if last_date:
                inferred_date = last_date + timedelta(days=1)
            elif plan_start_date:
                inferred_date = plan_start_date + timedelta(days=1)
            else:
                inferred_date = None

            if inferred_date:
                filled_dates[task["id"]] = inferred_date.strftime("%Y-%m-%d")
                last_date = inferred_date

        next_date = None
        for task in reversed(tasks):
            current_date = to_date(task.get("task_date"))
            if current_date:
                next_date = current_date
                continue

            if task["id"] in filled_dates:
                next_date = to_date(filled_dates[task["id"]])
                continue

            if next_date:
                inferred_date = next_date - timedelta(days=1)
                filled_dates[task["id"]] = inferred_date.strftime("%Y-%m-%d")
                next_date = inferred_date

        if not filled_dates:
            continue

        for task_id, task_date in filled_dates.items():
            execute("UPDATE learning_task SET task_date=%s WHERE id=%s", (task_date, task_id))
            total_updated += 1

        print(f"计划 {plan['id']} {plan['title']} 回填 {len(filled_dates)} 条任务日期")

    print(f"总计回填 {total_updated} 条学习任务日期")


if __name__ == "__main__":
    main()