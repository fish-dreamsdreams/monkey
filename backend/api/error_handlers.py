"""统一异常处理。

职责：把所有可预期与未预期错误转换成统一的 {data, error, meta} JSON。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.config import get_settings
from backend.core.error_codes import ErrorCode
from backend.core.exceptions import AppError
from backend.schemas.common import ApiResponse, ErrorBody, FieldError

logger = logging.getLogger("sanguo.editor")


def error_payload(
    *,
    code: str,
    message: str,
    details: list[FieldError] | None = None,
) -> dict[str, object]:
    """构造错误响应字典。"""
    body = ApiResponse[None](error=ErrorBody(code=code, message=message, details=details))
    return body.model_dump()


def register_error_handlers(app: FastAPI) -> None:
    """向 FastAPI 应用注册统一错误处理器。"""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        details = [FieldError(field=exc.field, message=exc.message)] if exc.field else None
        return JSONResponse(
            status_code=exc.http_status,
            content=error_payload(code=exc.code, message=exc.message, details=details),
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            FieldError(field=".".join(str(part) for part in err.get("loc", [])), message=str(err.get("msg")))
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code=ErrorCode.REQUEST_VALIDATION_ERROR.value,
                message="请求参数不合法",
                details=details,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        logger.exception("未处理异常: %s", exc)
        message = str(exc) if get_settings().debug else "服务器内部错误"
        return JSONResponse(
            status_code=500,
            content=error_payload(code=ErrorCode.INTERNAL_ERROR.value, message=message),
        )
