"""项目史料目录 API。"""

from fastapi import APIRouter, Depends, status

from backend.api.context import ProjectContext, get_project_context, valid_source_id
from backend.api.deps import get_source_service
from backend.schemas.common import ApiResponse
from backend.schemas.source import SourceCreate, SourceRead, SourceUpdate
from backend.services.source_service import SourceService

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["sources"])


@router.get("")
async def list_sources(
    ctx: ProjectContext = Depends(get_project_context),
    service: SourceService = Depends(get_source_service),
) -> ApiResponse[list[SourceRead]]:
    """列出项目史料目录，含系统预置的三国志与三国演义。"""
    data = await service.list_sources(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    ctx: ProjectContext = Depends(get_project_context),
    service: SourceService = Depends(get_source_service),
) -> ApiResponse[SourceRead]:
    """新增自定义来源。书名含「三国演义」时必须标记为 literary。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.put("/{source_id}")
async def update_source(
    payload: SourceUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    source_id: str = Depends(valid_source_id),
    service: SourceService = Depends(get_source_service),
) -> ApiResponse[SourceRead]:
    """更新自定义来源。"""
    data = await service.update(ctx.id, source_id, payload)
    return ApiResponse(data=data)


@router.delete("/{source_id}")
async def delete_source(
    ctx: ProjectContext = Depends(get_project_context),
    source_id: str = Depends(valid_source_id),
    service: SourceService = Depends(get_source_service),
) -> ApiResponse[None]:
    """删除自定义来源。"""
    await service.delete(ctx.id, source_id)
    return ApiResponse(data=None, meta={"deleted": True})
