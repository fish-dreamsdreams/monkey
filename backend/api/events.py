"""历史事件 API。后果仅为数据，不结算游戏。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_event_faction_id,
    valid_event_id,
    valid_event_participant_id,
    valid_event_source_id,
)
from backend.api.deps import get_event_service
from backend.schemas.common import ApiResponse
from backend.schemas.event import (
    EventFactionRead,
    EventFactionWrite,
    EventParticipantRead,
    EventParticipantWrite,
    EventRead,
    EventSourceRead,
    EventSourceWrite,
    EventSummary,
    EventWrite,
)
from backend.services.event_service import EventService

router = APIRouter(prefix="/projects/{project_id}", tags=["events"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventRead]:
    """创建历史或演义事件。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/events")
async def list_events(
    year: int | None = Query(default=None, ge=-500, le=3000),
    from_year: int | None = Query(default=None, ge=-500, le=3000),
    to_year: int | None = Query(default=None, ge=-500, le=3000),
    ctx: ProjectContext = Depends(get_project_context),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[list[EventSummary]]:
    """按年份列出事件。"""
    data = await service.list_events(ctx.id, year=year, from_year=from_year, to_year=to_year)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/events/{event_id}")
async def get_event(
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventRead]:
    """获取事件详情。"""
    data = await service.get(ctx.id, event_id)
    return ApiResponse(data=data)


@router.put("/events/{event_id}")
async def update_event(
    payload: EventWrite,
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventRead]:
    """更新事件。"""
    data = await service.update(ctx.id, event_id, payload)
    return ApiResponse(data=data)


@router.delete("/events/{event_id}")
async def delete_event(
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[None]:
    """删除事件。"""
    await service.delete(ctx.id, event_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/events/{event_id}/participants", status_code=status.HTTP_201_CREATED)
async def add_participant(
    payload: EventParticipantWrite,
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventParticipantRead]:
    """人物参与事件（校验生卒）。"""
    data = await service.add_participant(ctx.id, event_id, payload)
    return ApiResponse(data=data)


@router.delete("/events/{event_id}/participants/{participant_id}")
async def delete_participant(
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    participant_id: str = Depends(valid_event_participant_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[None]:
    """移除参与者。"""
    await service.delete_participant(ctx.id, event_id, participant_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/events/{event_id}/factions", status_code=status.HTTP_201_CREATED)
async def add_faction(
    payload: EventFactionWrite,
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventFactionRead]:
    """势力牵涉事件。"""
    data = await service.add_faction(ctx.id, event_id, payload)
    return ApiResponse(data=data)


@router.delete("/events/{event_id}/factions/{link_id}")
async def delete_faction(
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    link_id: str = Depends(valid_event_faction_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[None]:
    """移除势力牵涉。"""
    await service.delete_faction(ctx.id, event_id, link_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/events/{event_id}/sources", status_code=status.HTTP_201_CREATED)
async def add_source(
    payload: EventSourceWrite,
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[EventSourceRead]:
    """为事件挂史源。"""
    data = await service.add_source(ctx.id, event_id, payload)
    return ApiResponse(data=data)


@router.delete("/events/{event_id}/sources/{citation_id}")
async def delete_source(
    ctx: ProjectContext = Depends(get_project_context),
    event_id: str = Depends(valid_event_id),
    citation_id: str = Depends(valid_event_source_id),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[None]:
    """移除事件引文。"""
    await service.delete_source(ctx.id, event_id, citation_id)
    return ApiResponse(data=None, meta={"deleted": True})
