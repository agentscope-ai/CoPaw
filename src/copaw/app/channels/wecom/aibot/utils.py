"""
通用工具方法

对标 Node.js SDK src/utils.ts
"""

import os
import time


def generate_random_string(length: int = 8) -> str:
    """
    生成随机字符串

    :param length: 随机字符串长度，默认 8
    :return: 随机十六进制字符串
    """
    return os.urandom((length + 1) // 2).hex()[:length]


def generate_req_id(prefix: str) -> str:
    """
    生成唯一请求 ID

    格式：{prefix}_{timestamp}_{random}

    :param prefix: 前缀，通常为 cmd 名称
    :return: 唯一请求 ID
    """
    timestamp = int(time.time() * 1000)
    random_str = generate_random_string()
    return f"{prefix}_{timestamp}_{random_str}"
