"""ID 生成。"""

from uuid import uuid4


def new_id() -> str:
    """生成 UUID 主键字符串。"""
    return str(uuid4())
