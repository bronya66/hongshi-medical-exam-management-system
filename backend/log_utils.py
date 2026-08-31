"""
日志工具：
1. 初始化接口请求日志（滚动文件 + 控制台）
2. 输出统一格式请求日志，便于答辩演示与排障
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler

from utils import ensure_dir


class RequestLoggingFilter(logging.Filter):
    def filter(self, record):
        # 保证缺失字段不会导致格式化失败
        for key in ["request_id", "method", "path", "status", "latency_ms", "ip", "user", "detail"]:
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True


def _mask_sensitive(payload):
    if not isinstance(payload, dict):
        return payload
    masked = dict(payload)
    for key in ["password", "new_password", "old_password"]:
        if key in masked:
            masked[key] = "***"
    return masked


def build_request_detail(args_dict, json_body):
    data = {
        "query": args_dict or {},
        "json": _mask_sensitive(json_body) if isinstance(json_body, dict) else {},
    }
    text = json.dumps(data, ensure_ascii=False)
    return text[:1200]


def init_request_logger(base_dir):
    logs_dir = os.path.join(base_dir, "logs")
    ensure_dir(logs_dir)
    log_file = os.path.join(logs_dir, "api.log")

    logger = logging.getLogger("api_request")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | req=%(request_id)s | %(method)s %(path)s | status=%(status)s | %(latency_ms)sms | ip=%(ip)s | user=%(user)s | %(detail)s"
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestLoggingFilter())

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(RequestLoggingFilter())

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
