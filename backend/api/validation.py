"""跨实体校验 API。只读报告，不改内容。"""

from fastapi import APIRouter, Depends, Query

from backend.api.context import ProjectContext, get_project_context
from backend.api.deps import get_validation_service
from backend.schemas.common import ApiResponse
from backend.schemas.validation import ValidationReportRead
from backend.services.validation_service import ValidationService
from backend.validation.types import ValidationMode

router = APIRouter(prefix="/projects/{project_id}", tags=["validation"])


@router.get("/validation")
async def validate_project(
    ctx: ProjectContext = Depends(get_project_context),
    mode: ValidationMode = Query(default=ValidationMode.STRICT_HISTORICAL),
    service: ValidationService = Depends(get_validation_service),
) -> ApiResponse[ValidationReportRead]:
    """扫描时间线、易主重叠与剧情死循环。"""
    data = await service.validate(ctx.id, mode)
    return ApiResponse(
        data=data,
        meta={"mode": mode.value, "valid": data.valid, "error_count": data.error_count},
    )
