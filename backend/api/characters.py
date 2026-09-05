"""人物 API。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_character_id,
    valid_citation_id,
)
from backend.api.deps import get_character_service
from backend.schemas.character import CharacterCreate, CharacterRead, CharacterSummary, CharacterUpdate
from backend.schemas.common import ApiResponse
from backend.schemas.source import CharacterSourceRead, CharacterSourceWrite
from backend.services.character_service import CharacterService

router = APIRouter(prefix="/projects/{project_id}/characters", tags=["characters"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_character(
    payload: CharacterCreate,
    ctx: ProjectContext = Depends(get_project_context),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """创建人物。请求体分为 base / historical / game 三栏。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("")
async def list_characters(
    ctx: ProjectContext = Depends(get_project_context),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[list[CharacterSummary]]:
    """分页列出人物摘要。"""
    items, total = await service.list_characters(ctx.id, skip, limit)
    return ApiResponse(data=items, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/{character_id}")
async def get_character(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """获取人物详情。"""
    data = await service.get(ctx.id, character_id)
    return ApiResponse(data=data)


@router.put("/{character_id}")
async def update_character(
    payload: CharacterUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """全量更新人物。游戏栏不会覆盖历史栏。"""
    data = await service.update(ctx.id, character_id, payload)
    return ApiResponse(data=data)


@router.delete("/{character_id}", status_code=status.HTTP_200_OK)
async def delete_character(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[None]:
    """删除人物。"""
    await service.delete(ctx.id, character_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/{character_id}/sources", status_code=status.HTTP_201_CREATED)
async def add_character_source(
    payload: CharacterSourceWrite,
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterSourceRead]:
    """为人物追加引文。演义不得挂到 historical 层。"""
    data = await service.add_citation(ctx.id, character_id, payload)
    return ApiResponse(data=data)


@router.delete("/{character_id}/sources/{citation_id}", status_code=status.HTTP_200_OK)
async def delete_character_source(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    citation_id: str = Depends(valid_citation_id),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[None]:
    """删除人物引文。"""
    await service.delete_citation(ctx.id, character_id, citation_id)
    return ApiResponse(data=None, meta={"deleted": True})
