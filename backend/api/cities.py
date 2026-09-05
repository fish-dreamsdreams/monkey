"""城池 API。归属仅在指定年份时派生。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import ProjectContext, get_project_context, valid_city_id
from backend.api.deps import get_city_service
from backend.schemas.city import CityRead, CityWrite
from backend.schemas.common import ApiResponse
from backend.services.city_service import CityService

router = APIRouter(prefix="/projects/{project_id}", tags=["cities"])


@router.post("/cities", status_code=status.HTTP_201_CREATED)
async def create_city(
    payload: CityWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: CityService = Depends(get_city_service),
) -> ApiResponse[CityRead]:
    """创建城池。不写入当前归属。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/cities")
async def list_cities(
    at_year: int | None = Query(default=None, ge=-500, le=3000),
    ctx: ProjectContext = Depends(get_project_context),
    service: CityService = Depends(get_city_service),
) -> ApiResponse[list[CityRead]]:
    """列出城池；可按年份填充 owner。"""
    data = await service.list_cities(ctx.id, at_year=at_year)
    return ApiResponse(data=data, meta={"total": len(data), "at_year": at_year})


@router.get("/cities/{city_id}")
async def get_city(
    at_year: int | None = Query(default=None, ge=-500, le=3000),
    ctx: ProjectContext = Depends(get_project_context),
    city_id: str = Depends(valid_city_id),
    service: CityService = Depends(get_city_service),
) -> ApiResponse[CityRead]:
    """获取城池。"""
    data = await service.get(ctx.id, city_id, at_year=at_year)
    return ApiResponse(data=data, meta={"at_year": at_year})


@router.put("/cities/{city_id}")
async def update_city(
    payload: CityWrite,
    ctx: ProjectContext = Depends(get_project_context),
    city_id: str = Depends(valid_city_id),
    service: CityService = Depends(get_city_service),
) -> ApiResponse[CityRead]:
    """更新城池。"""
    data = await service.update(ctx.id, city_id, payload)
    return ApiResponse(data=data)


@router.delete("/cities/{city_id}")
async def delete_city(
    ctx: ProjectContext = Depends(get_project_context),
    city_id: str = Depends(valid_city_id),
    service: CityService = Depends(get_city_service),
) -> ApiResponse[None]:
    """删除城池。"""
    await service.delete(ctx.id, city_id)
    return ApiResponse(data=None, meta={"deleted": True})
