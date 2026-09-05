"""势力、成员、领土与某年视图 API。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_faction_id,
    valid_faction_member_id,
    valid_faction_territory_id,
)
from backend.api.deps import get_faction_service
from backend.schemas.common import ApiResponse
from backend.schemas.faction import (
    FactionMemberRead,
    FactionMemberWrite,
    FactionRead,
    FactionTerritoryRead,
    FactionTerritoryWrite,
    FactionWrite,
    YearView,
)
from backend.services.faction_service import FactionService

router = APIRouter(prefix="/projects/{project_id}", tags=["factions"])


@router.get("/year-view")
async def get_year_view(
    year: int = Query(ge=-500, le=3000),
    ctx: ProjectContext = Depends(get_project_context),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[YearView]:
    """按年份派生城池归属与在势成员。"""
    data = await service.year_view(ctx.id, year)
    return ApiResponse(data=data)


@router.post("/factions", status_code=status.HTTP_201_CREATED)
async def create_faction(
    payload: FactionWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[FactionRead]:
    """创建用户势力。编辑器不预置魏蜀吴。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/factions")
async def list_factions(
    ctx: ProjectContext = Depends(get_project_context),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[list[FactionRead]]:
    """列出项目势力。"""
    data = await service.list_factions(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/factions/{faction_id}")
async def get_faction(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[FactionRead]:
    """获取势力。"""
    data = await service.get(ctx.id, faction_id)
    return ApiResponse(data=data)


@router.put("/factions/{faction_id}")
async def update_faction(
    payload: FactionWrite,
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[FactionRead]:
    """更新势力。"""
    data = await service.update(ctx.id, faction_id, payload)
    return ApiResponse(data=data)


@router.delete("/factions/{faction_id}")
async def delete_faction(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[None]:
    """删除势力。"""
    await service.delete(ctx.id, faction_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/factions/{faction_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    payload: FactionMemberWrite,
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[FactionMemberRead]:
    """人物入势。"""
    data = await service.add_member(ctx.id, faction_id, payload)
    return ApiResponse(data=data)


@router.get("/factions/{faction_id}/members")
async def list_members(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[list[FactionMemberRead]]:
    """列出成员记录。"""
    data = await service.list_members(ctx.id, faction_id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.delete("/factions/{faction_id}/members/{member_id}")
async def delete_member(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    member_id: str = Depends(valid_faction_member_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[None]:
    """删除成员记录。"""
    await service.delete_member(ctx.id, faction_id, member_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/factions/{faction_id}/territories", status_code=status.HTTP_201_CREATED)
async def add_territory(
    payload: FactionTerritoryWrite,
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[FactionTerritoryRead]:
    """城池按时段归属该势力。"""
    data = await service.add_territory(ctx.id, faction_id, payload)
    return ApiResponse(data=data)


@router.get("/factions/{faction_id}/territories")
async def list_territories(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[list[FactionTerritoryRead]]:
    """列出领土记录。"""
    data = await service.list_territories(ctx.id, faction_id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.delete("/factions/{faction_id}/territories/{territory_id}")
async def delete_territory(
    ctx: ProjectContext = Depends(get_project_context),
    faction_id: str = Depends(valid_faction_id),
    territory_id: str = Depends(valid_faction_territory_id),
    service: FactionService = Depends(get_faction_service),
) -> ApiResponse[None]:
    """删除领土记录。"""
    await service.delete_territory(ctx.id, faction_id, territory_id)
    return ApiResponse(data=None, meta={"deleted": True})
