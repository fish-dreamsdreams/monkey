"""时间工具。"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """返回无时区的 UTC 时间，写入 DateTime 列。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
