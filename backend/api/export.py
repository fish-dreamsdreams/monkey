"""项目导入导出 API。导出必须先通过校验引擎。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import ProjectContext, get_project_context
from backend.api.deps import get_export_service
from backend.schemas.common import ApiResponse
from backend.schemas.export import ExportPackage, ExportResult
from backend.schemas.project import ProjectRead
from backend.services.export_service import ExportService
from backend.validation.types import ValidationMode

router = APIRouter(tags=["export"])


@router.post("/projects/import", status_code=status.HTTP_201_CREATED)
async def import_project(
    payload: ExportPackage,
    service: ExportService = Depends(get_export_service),
) -> ApiResponse[ProjectRead]:
    """按 schema 与 checksum 导入为新项目。"""
    data = await service.import_package(payload)
    return ApiResponse(data=data, meta={"schema_version": data.schema_version})


@router.post("/projects/{project_id}/export")
async def export_project(
    ctx: ProjectContext = Depends(get_project_context),
    mode: ValidationMode = Query(default=ValidationMode.STRICT_HISTORICAL),
    service: ExportService = Depends(get_export_service),
) -> ApiResponse[ExportResult]:
    """校验通过后生成客户端可读包并写入 exports/。"""
    data = await service.export_project(ctx.id, mode)
    return ApiResponse(
        data=data,
        meta={
            "mode": mode.value,
            "schema_version": data.package.manifest.schema_version,
            "content_version": data.package.manifest.content_version,
        },
    )
