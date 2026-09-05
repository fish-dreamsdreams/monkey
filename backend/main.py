"""FastAPI 入口。

职责：装配路由与异常处理，不承载业务逻辑。
"""

from fastapi import FastAPI

from backend.api.error_handlers import register_error_handlers
from backend.api.router import api_router
from backend.core.schema_version import API_VERSION, CURRENT_SCHEMA_VERSION
from backend.schemas.common import ApiResponse

app = FastAPI(
    title="三国内容编辑器",
    version=API_VERSION,
    description="Phase 2：公共基础设施。人物史实与游戏设定分栏存储。",
)
register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> ApiResponse[dict[str, str]]:
    """存活检查，附带当前 schema 版本。不探测 MySQL，便于测试与启动探活。"""
    return ApiResponse(data={"status": "ok", "schema_version": CURRENT_SCHEMA_VERSION, "api_version": API_VERSION})
