"""稳定错误码。

职责：集中声明 API 错误码，避免各模块硬编码字符串。
"""

from enum import Enum


class ErrorCode(str, Enum):
    """对外错误码。"""

    APP_ERROR = "app_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation_error"
    INVALID_ID = "invalid_id"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    REQUEST_VALIDATION_ERROR = "request_validation_error"
    INTERNAL_ERROR = "internal_error"
