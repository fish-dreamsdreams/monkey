"""应用异常。

职责：把领域/仓储错误映射为稳定的业务异常，供 API 层转换成 HTTP 响应。
"""

from backend.core.error_codes import ErrorCode


class AppError(Exception):
    """可预期的业务错误基类。"""

    http_status: int = 400
    default_code: str = ErrorCode.APP_ERROR.value

    def __init__(
        self,
        message: str,
        code: str | None = None,
        field: str | None = None,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.field = field
        self.details = details


class NotFoundError(AppError):
    """资源不存在。"""

    http_status = 404
    default_code = ErrorCode.NOT_FOUND.value

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConflictError(AppError):
    """唯一性或状态冲突。"""

    http_status = 409
    default_code = ErrorCode.CONFLICT.value

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ValidationError(AppError):
    """领域校验失败。"""

    http_status = 400
    default_code = ErrorCode.VALIDATION_ERROR.value

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, field=field)


class InvalidIdError(AppError):
    """实体 ID 格式不符合前缀规则。"""

    http_status = 400
    default_code = ErrorCode.INVALID_ID.value

    def __init__(self, message: str, field: str = "id") -> None:
        super().__init__(message, field=field)


class UnsupportedSchemaError(AppError):
    """项目 schema_version 不被当前编辑器支持。"""

    http_status = 409
    default_code = ErrorCode.UNSUPPORTED_SCHEMA.value

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExportBlockedError(AppError):
    """校验未通过，禁止导出客户端包。"""

    http_status = 409
    default_code = ErrorCode.EXPORT_BLOCKED.value

    def __init__(self, details: list[dict[str, str]]) -> None:
        super().__init__("校验未通过，不能导出", details=details)
