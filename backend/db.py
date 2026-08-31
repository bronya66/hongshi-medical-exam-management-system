"""
数据库连接模块。
负责：
1. 统一 MySQL 连接配置
2. 提供查询与写入的基础方法
3. 降低 app.py 中的重复数据库代码
"""

import pymysql
from pymysql.cursors import DictCursor

# 数据库连接配置（按需求固定）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "558000",
    "database": "hongshi_db",
    "port": 3306,
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": False,
}


def get_connection():
    """创建并返回一个新的数据库连接。"""
    return pymysql.connect(**DB_CONFIG)


def query_all(sql, params=None):
    """
    执行查询并返回多行结果。

    :param sql: SQL 语句
    :param params: 参数元组/列表
    :return: list[dict]
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def query_one(sql, params=None):
    """
    执行查询并返回单行结果。

    :param sql: SQL 语句
    :param params: 参数元组/列表
    :return: dict | None
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()


def execute(sql, params=None):
    """
    执行写操作（INSERT/UPDATE/DELETE）。

    :param sql: SQL 语句
    :param params: 参数元组/列表
    :return: 受影响行数
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params or ())
        conn.commit()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_and_get_id(sql, params=None):
    """
    执行插入并返回新纪录 ID。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            new_id = cursor.lastrowid
        conn.commit()
        return new_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
