"""人物 API。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import get_character_service
from backend.schemas.character import CharacterCreate, CharacterRead, CharacterSummary, CharacterUpdate
from backend.schemas.common import ApiResponse
from backend.services.character_service import CharacterService

router = APIRouter(prefix="/projects/{project_id}/characters", tags=["characters"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_character(
    project_id: str,
    payload: CharacterCreate,
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """创建人物。请求体分为 base / historical / game 三栏。"""
    data = await service.create(project_id, payload)
    return ApiResponse(data=data)


@router.get("")
async def list_characters(
    project_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[list[CharacterSummary]]:
    """分页列出人物摘要。"""
    items, total = await service.list_characters(project_id, skip, limit)
    return ApiResponse(data=items, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/{character_id}")
async def get_character(
    project_id: str,
    character_id: str,
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """获取人物详情。"""
    data = await service.get(project_id, character_id)
    return ApiResponse(data=data)


@router.put("/{character_id}")
async def update_character(
    project_id: str,
    character_id: str,
    payload: CharacterUpdate,
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[CharacterRead]:
    """全量更新人物。游戏栏不会覆盖历史栏。"""
    data = await service.update(project_id, character_id, payload)
    return ApiResponse(data=data)


@router.delete("/{character_id}", status_code=status.HTTP_200_OK)
async def delete_character(
    project_id: str,
    character_id: str,
    service: CharacterService = Depends(get_character_service),
) -> ApiResponse[None]:
    """删除人物。"""
    await service.delete(project_id, character_id)
    return ApiResponse(data=None, meta={"deleted": True})
