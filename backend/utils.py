"""
工具函数模块。
包含：
1. 时间格式化
2. 文件上传存储
3. 违规词屏蔽
"""

import os
import uuid
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from werkzeug.utils import secure_filename


DEFAULT_FORBIDDEN_WORDS = {
    "赌博",
    "色情",
    "毒品",
    "诈骗",
    "违法",
    "暴力",
    "枪支",
    "炸弹",
    "傻逼",
    "妈的",
}


@lru_cache(maxsize=1)
def load_forbidden_words():
    """加载违规词词库，优先读取同目录 forbidden_words.txt。"""
    words = set(DEFAULT_FORBIDDEN_WORDS)
    word_file = Path(__file__).resolve().with_name("forbidden_words.txt")
    if word_file.exists():
        for line in word_file.read_text(encoding="utf-8").splitlines():
            word = line.strip()
            if word and not word.startswith("#"):
                words.add(word)
    return sorted(words, key=len, reverse=True)


def mask_forbidden_text(text, replacement="*"):
    """将文本中的违规词替换为指定字符。"""
    if text is None:
        return text
    value = str(text)
    for word in load_forbidden_words():
        if not word:
            continue
        value = value.replace(word, replacement * len(word))
    return value


def contains_forbidden_text(text):
    """判断文本是否包含违规词。"""
    if not text:
        return False
    value = str(text)
    return any(word and word in value for word in load_forbidden_words())


def first_forbidden_word(text):
    """返回文本中命中的第一个违规词，未命中返回 None。"""
    if not text:
        return None
    value = str(text)
    for word in load_forbidden_words():
        if word and word in value:
            return word
    return None


def now_str():
    """返回当前时间字符串，格式：YYYY-MM-DD HH:MM:SS"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path):
    """确保目录存在，不存在则自动创建。"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def save_upload_file(file_storage, upload_dir):
    """
    保存上传文件到指定目录，并返回保存后的文件名。

    :param file_storage: Flask request.files 中的文件对象
    :param upload_dir: 上传目录绝对路径
    :return: str 保存后的文件名
    """
    ensure_dir(upload_dir)

    raw_name = (file_storage.filename or "").strip()

    # 先尝试从原始文件名提取扩展名，兼容中文文件名。
    ext = Path(raw_name).suffix.lower()

    # 若原始文件名取不到扩展名，再尝试安全文件名兜底。
    if not ext:
        safe_name = secure_filename(raw_name or "file")
        ext = Path(safe_name).suffix.lower()

    # 仅保留常规扩展名，避免异常后缀注入。
    if not re.fullmatch(r"\.[a-z0-9]{1,12}", ext):
        ext = ""

    # 使用 UUID + 时间戳避免重名覆盖
    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(upload_dir, unique_name)

    file_storage.save(target_path)
    return unique_name
