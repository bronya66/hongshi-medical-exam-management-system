import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import execute, query_all, query_one


def rename_users():
    username_map = {
        "test_teacher1": "周凯",
        "test_teacher2": "陈洁",
        "test_teacher3": "王雪",
        "test_supervisor1": "孙华",
        "test_supervisor2": "刘颖",
        "test_student1": "张晨",
        "test_student2": "李悦",
        "test_student3": "王涵",
        "test_student4": "陈诺",
        "test_student5": "赵宁",
        "test_student6": "孙博",
        "test_student7": "周妍",
        "test_student8": "吴凯",
    }

    for old_name, new_name in username_map.items():
        exists = query_one("SELECT id FROM users WHERE username=%s", (old_name,))
        conflict = query_one("SELECT id FROM users WHERE username=%s", (new_name,))
        if exists and not conflict:
            execute("UPDATE users SET username=%s WHERE username=%s", (new_name, old_name))


def rationalize_teacher_relations():
    teacher01 = query_one("SELECT id FROM users WHERE username='李明'")
    teacher_clinical = query_one("SELECT id FROM users WHERE username='周凯'")
    teacher_basic = query_one("SELECT id FROM users WHERE username='陈洁'")
    teacher_oral = query_one("SELECT id FROM users WHERE username='王雪'")

    if not (teacher01 and teacher_clinical and teacher_basic and teacher_oral):
        return

    teacher_ids = [teacher01["id"], teacher_clinical["id"], teacher_basic["id"], teacher_oral["id"]]

    student_users = query_all(
        """
        SELECT id FROM users
        WHERE username IN (
            '张晨','李悦','王涵','陈诺',
            '赵宁','孙博','周妍','吴凯'
        )
        ORDER BY id
        """
    )

    for index, row in enumerate(student_users):
        teacher_id = teacher_ids[index % len(teacher_ids)]
        execute("UPDATE student_info SET teacher_id=%s WHERE user_id=%s", (teacher_id, row["id"]))

    homework_rows = query_all(
        "SELECT id FROM homework WHERE teacher_id IN (%s,%s,%s) ORDER BY id",
        (teacher_clinical["id"], teacher_basic["id"], teacher_oral["id"]),
    )
    for index, row in enumerate(homework_rows):
        execute("UPDATE homework SET teacher_id=%s WHERE id=%s", (teacher_ids[index % len(teacher_ids)], row["id"]))

    material_rows = query_all(
        "SELECT id FROM materials WHERE teacher_id IN (%s,%s,%s) ORDER BY id",
        (teacher_clinical["id"], teacher_basic["id"], teacher_oral["id"]),
    )
    for index, row in enumerate(material_rows):
        execute("UPDATE materials SET teacher_id=%s WHERE id=%s", (teacher_ids[index % len(teacher_ids)], row["id"]))

    evaluation_rows = query_all(
        "SELECT id, student_id, teacher_id FROM evaluation WHERE teacher_id=%s ORDER BY id",
        (teacher_clinical["id"],),
    )
    for row in evaluation_rows:
        conflict = query_one(
            "SELECT id FROM evaluation WHERE student_id=%s AND teacher_id=%s",
            (row["student_id"], teacher01["id"]),
        )
        if not conflict:
            execute("UPDATE evaluation SET teacher_id=%s WHERE id=%s", (teacher01["id"], row["id"]))


def rationalize_file_paths():
    replace_pairs = [
        ("test_teacher1", "周凯"),
        ("test_teacher2", "陈洁"),
        ("test_teacher3", "王雪"),
        ("test_student1", "张晨"),
        ("test_student2", "李悦"),
        ("test_student3", "王涵"),
        ("test_student4", "陈诺"),
        ("test_student5", "赵宁"),
        ("test_student6", "孙博"),
        ("test_student7", "周妍"),
        ("test_student8", "吴凯"),
    ]

    for old_text, new_text in replace_pairs:
        execute("UPDATE materials SET file_path=REPLACE(file_path,%s,%s) WHERE file_path LIKE %s", (old_text, new_text, f"%{old_text}%"))
        execute("UPDATE checkin SET file_path=REPLACE(file_path,%s,%s) WHERE file_path LIKE %s", (old_text, new_text, f"%{old_text}%"))
        execute("UPDATE homework_submission SET file_path=REPLACE(file_path,%s,%s) WHERE file_path LIKE %s", (old_text, new_text, f"%{old_text}%"))


def summary():
    p = "test_%"
    test_users = query_one("SELECT COUNT(*) AS total FROM users WHERE username LIKE %s", (p,))["total"]
    test_material_paths = query_one("SELECT COUNT(*) AS total FROM materials WHERE file_path LIKE %s", ("%test_%",))["total"]
    test_checkin_paths = query_one("SELECT COUNT(*) AS total FROM checkin WHERE file_path LIKE %s", ("%test_%",))["total"]
    role_dist = query_all("SELECT role, COUNT(*) AS total FROM users GROUP BY role ORDER BY role")
    teacher_dist = query_all("SELECT teacher_id, COUNT(*) AS total FROM student_info GROUP BY teacher_id ORDER BY teacher_id")
    eval_teacher_dist = query_all("SELECT teacher_id, COUNT(*) AS total FROM evaluation GROUP BY teacher_id ORDER BY teacher_id")

    return {
        "test_users_remaining": test_users,
        "test_material_paths_remaining": test_material_paths,
        "test_checkin_paths_remaining": test_checkin_paths,
        "role_distribution": role_dist,
        "student_teacher_distribution": teacher_dist,
        "evaluation_teacher_distribution": eval_teacher_dist,
    }


def main():
    rename_users()
    rationalize_teacher_relations()
    rationalize_file_paths()
    print("数据库 test 数据合理化完成")
    print(summary())


if __name__ == "__main__":
    main()
