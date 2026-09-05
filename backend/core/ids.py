"""实体 ID 规则。

职责：生成并校验带类型前缀的主键。业务 code（如 chr_liu_bei）与主键不是同一套规则。
主键格式：{3 位前缀}_{32 位 hex}，总长 36，可放入现有 String(36) 列。
"""

import re
from enum import Enum
from uuid import uuid4

from backend.core.exceptions import InvalidIdError

_ID_PATTERN = re.compile(r"^[a-z]{3}_[0-9a-f]{32}$")
_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class EntityPrefix(str, Enum):
    """主键类型前缀。"""

    PROJECT = "prj"
    CHARACTER = "chr"
    PERSONALITY_TAG = "tag"
    HISTORICAL_RECORD = "rec"
    ATTRIBUTE = "atr"
    SOURCE = "src"
    CITATION = "cit"


def new_id(prefix: EntityPrefix) -> str:
    """生成带前缀的 UUID 主键。"""
    return f"{prefix.value}_{uuid4().hex}"


def new_business_code(prefix: str) -> str:
    """在未指定业务 code 时生成可读短码。"""
    return f"{prefix}_{uuid4().hex[:10]}"


def require_id(value: str, prefix: EntityPrefix, field: str) -> str:
    """校验路径/字段中的实体 ID。格式错误抛出 InvalidIdError。"""
    expected = f"{prefix.value}_"
    if not _ID_PATTERN.fullmatch(value) or not value.startswith(expected):
        raise InvalidIdError(
            f"ID 格式必须为 {prefix.value}_ 后接 32 位小写十六进制",
            field=field,
        )
    return value


def is_valid_business_code(value: str) -> bool:
    """校验用户提供的业务 code。"""
    return bool(_CODE_PATTERN.fullmatch(value))
