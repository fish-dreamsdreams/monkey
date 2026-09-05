"""FastAPI 入口。

职责：装配路由与异常处理，不承载业务逻辑。
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.core.exceptions import AppError, ConflictError, NotFoundError, ValidationError
from backend.schemas.common import ApiResponse, ErrorBody, FieldError

app = FastAPI(
    title="三国内容编辑器",
    version="0.1.0",
    description="Phase 1：项目管理与人物管理。历史事实与游戏设定分栏存储。",
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """存活检查。"""
    return {"status": "ok"}


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    body = ApiResponse[None](error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=404, content=body.model_dump())


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    body = ApiResponse[None](error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=409, content=body.model_dump())


@app.exception_handler(ValidationError)
async def domain_validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    details = [FieldError(field=exc.field, message=exc.message)] if exc.field else None
    body = ApiResponse[None](error=ErrorBody(code=exc.code, message=exc.message, details=details))
    return JSONResponse(status_code=400, content=body.model_dump())


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    body = ApiResponse[None](error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=400, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def pydantic_validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        FieldError(field=".".join(str(part) for part in err.get("loc", [])), message=str(err.get("msg")))
        for err in exc.errors()
    ]
    body = ApiResponse[None](
        error=ErrorBody(code="request_validation_error", message="请求参数不合法", details=details)
    )
    return JSONResponse(status_code=422, content=body.model_dump())
