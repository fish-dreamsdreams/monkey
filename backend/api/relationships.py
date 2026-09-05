"""人物关系 API。"""

from fastapi import APIRouter, Depends, Query, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_character_id,
    valid_relationship_id,
)
from backend.api.deps import get_relationship_service
from backend.schemas.common import ApiResponse
from backend.schemas.relationship import (
    CharacterRelationshipGraph,
    RelationshipCreate,
    RelationshipRead,
    RelationshipUpdate,
)
from backend.services.relationship_service import RelationshipService

router = APIRouter(prefix="/projects/{project_id}", tags=["relationships"])


@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(
    payload: RelationshipCreate,
    ctx: ProjectContext = Depends(get_project_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[RelationshipRead]:
    """创建人物关系。结义、婚姻等对称类型会同时写入反向边。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/relationships")
async def list_relationships(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str | None = Query(default=None),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[list[RelationshipRead]]:
    """列出项目关系主边。可按人物过滤。"""
    data = await service.list_relationships(ctx.id, character_id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/relationships/{relationship_id}")
async def get_relationship(
    ctx: ProjectContext = Depends(get_project_context),
    relationship_id: str = Depends(valid_relationship_id),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[RelationshipRead]:
    """获取单条关系。"""
    data = await service.get(ctx.id, relationship_id)
    return ApiResponse(data=data)


@router.put("/relationships/{relationship_id}")
async def update_relationship(
    payload: RelationshipUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    relationship_id: str = Depends(valid_relationship_id),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[RelationshipRead]:
    """更新关系类型、亲密度与年代。两端人物不可改。"""
    data = await service.update(ctx.id, relationship_id, payload)
    return ApiResponse(data=data)


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    ctx: ProjectContext = Depends(get_project_context),
    relationship_id: str = Depends(valid_relationship_id),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[None]:
    """删除关系及其对称反向边。"""
    await service.delete(ctx.id, relationship_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.get("/characters/{character_id}/relationships")
async def get_character_relationship_graph(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: RelationshipService = Depends(get_relationship_service),
) -> ApiResponse[CharacterRelationshipGraph]:
    """人物关系邻接表，供编辑器画关系图。"""
    data = await service.graph_for_character(ctx.id, character_id)
    return ApiResponse(data=data, meta={"total": len(data.edges)})
