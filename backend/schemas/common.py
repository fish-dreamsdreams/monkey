"""通用 API 结构。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class FieldError(BaseModel):
    """单个字段错误。"""

    field: str
    message: str


class ErrorBody(BaseModel):
    """错误正文。"""

    code: str
    message: str
    details: list[FieldError] | None = None


class ApiResponse(BaseModel, Generic[T]):
    """统一响应包裹。"""

    data: T | None = None
    error: ErrorBody | None = None
    meta: dict[str, object] | None = None


class PaginationMeta(BaseModel):
    """列表分页信息。"""

    total: int
    skip: int = 0
    limit: int = Field(default=50, ge=1, le=200)
