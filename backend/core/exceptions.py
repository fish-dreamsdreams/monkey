"""应用异常。

职责：把领域/仓储错误映射为稳定的业务异常，供 API 层转换成 HTTP 响应。
"""


class AppError(Exception):
    """可预期的业务错误基类。"""

    def __init__(self, message: str, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(AppError):
    """资源不存在。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class ConflictError(AppError):
    """唯一性或状态冲突。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict")


class ValidationError(AppError):
    """领域校验失败。"""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, code="validation_error")
        self.field = field
