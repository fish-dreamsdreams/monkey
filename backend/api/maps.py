"""地图 API。地形按图层分块提交，不做 Canvas 渲染。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_city_id,
    valid_map_feature_id,
    valid_map_id,
)
from backend.api.deps import get_map_service
from backend.schemas.common import ApiResponse
from backend.schemas.map import (
    MapCityPlace,
    MapCityRead,
    MapFeatureRead,
    MapFeatureWrite,
    MapRead,
    MapSummary,
    MapWrite,
    TerrainCellRead,
    TerrainPatchWrite,
)
from backend.services.map_service import MapService

router = APIRouter(prefix="/projects/{project_id}", tags=["maps"])


@router.post("/maps", status_code=status.HTTP_201_CREATED)
async def create_map(
    payload: MapWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapRead]:
    """创建空白地图。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/maps")
async def list_maps(
    ctx: ProjectContext = Depends(get_project_context),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[list[MapSummary]]:
    """列出项目地图。"""
    data = await service.list_maps(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/maps/{map_id}")
async def get_map(
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapRead]:
    """获取地图元数据、城池与地物。"""
    data = await service.get(ctx.id, map_id)
    return ApiResponse(data=data)


@router.put("/maps/{map_id}")
async def update_map(
    payload: MapWrite,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapRead]:
    """更新地图尺寸与默认地形。"""
    data = await service.update(ctx.id, map_id, payload)
    return ApiResponse(data=data)


@router.delete("/maps/{map_id}")
async def delete_map(
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[None]:
    """删除地图。"""
    await service.delete(ctx.id, map_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.get("/maps/{map_id}/terrain")
async def list_terrain(
    x_min: int | None = Query(default=None, ge=0, le=255),
    y_min: int | None = Query(default=None, ge=0, le=255),
    x_max: int | None = Query(default=None, ge=0, le=255),
    y_max: int | None = Query(default=None, ge=0, le=255),
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[list[TerrainCellRead]]:
    """读取稀疏地形覆盖。"""
    data = await service.list_terrain(ctx.id, map_id, x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.patch("/maps/{map_id}/terrain")
async def patch_terrain(
    payload: TerrainPatchWrite,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[list[TerrainCellRead]]:
    """分块更新地形。terrain 为空表示恢复默认。"""
    data = await service.patch_terrain(ctx.id, map_id, payload)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.post("/maps/{map_id}/features", status_code=status.HTTP_201_CREATED)
async def add_feature(
    payload: MapFeatureWrite,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapFeatureRead]:
    """新增区域、道路、河流或山脉。"""
    data = await service.add_feature(ctx.id, map_id, payload)
    return ApiResponse(data=data)


@router.put("/maps/{map_id}/features/{feature_id}")
async def update_feature(
    payload: MapFeatureWrite,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    feature_id: str = Depends(valid_map_feature_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapFeatureRead]:
    """更新地物。"""
    data = await service.update_feature(ctx.id, map_id, feature_id, payload)
    return ApiResponse(data=data)


@router.delete("/maps/{map_id}/features/{feature_id}")
async def delete_feature(
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    feature_id: str = Depends(valid_map_feature_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[None]:
    """删除地物。"""
    await service.delete_feature(ctx.id, map_id, feature_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/maps/{map_id}/cities", status_code=status.HTTP_201_CREATED)
async def place_city(
    payload: MapCityPlace,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[MapCityRead]:
    """把城池挂到地图格子。"""
    data = await service.place_city(ctx.id, map_id, payload)
    return ApiResponse(data=data)


@router.delete("/maps/{map_id}/cities/{city_id}")
async def unplace_city(
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    city_id: str = Depends(valid_city_id),
    service: MapService = Depends(get_map_service),
) -> ApiResponse[None]:
    """从地图卸下城池。"""
    await service.unplace_city(ctx.id, map_id, city_id)
    return ApiResponse(data=None, meta={"deleted": True})
