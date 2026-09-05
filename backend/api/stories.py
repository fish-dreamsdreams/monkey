"""剧情 API。节点图只存数据，不演出、不战斗。"""

from fastapi import APIRouter, Depends, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_story_action_id,
    valid_story_cast_id,
    valid_story_chapter_id,
    valid_story_choice_id,
    valid_story_condition_id,
    valid_story_edge_id,
    valid_story_id,
    valid_story_node_id,
)
from backend.api.deps import get_story_service
from backend.schemas.common import ApiResponse
from backend.schemas.story import (
    StoryActionRead,
    StoryActionWrite,
    StoryCastRead,
    StoryCastWrite,
    StoryChapterRead,
    StoryChapterWrite,
    StoryChoiceRead,
    StoryChoiceWrite,
    StoryConditionRead,
    StoryConditionWrite,
    StoryEdgeRead,
    StoryEdgeWrite,
    StoryNodeRead,
    StoryNodeWrite,
    StoryRead,
    StorySummary,
    StoryWrite,
)
from backend.services.story_service import StoryService

router = APIRouter(prefix="/projects/{project_id}", tags=["stories"])


@router.post("/stories", status_code=status.HTTP_201_CREATED)
async def create_story(
    payload: StoryWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryRead]:
    """创建空剧情。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/stories")
async def list_stories(
    ctx: ProjectContext = Depends(get_project_context),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[list[StorySummary]]:
    """列出剧情。"""
    data = await service.list_stories(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/stories/{story_id}")
async def get_story(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryRead]:
    """获取剧情节点图与环检测结果。"""
    data = await service.get(ctx.id, story_id)
    return ApiResponse(data=data)


@router.put("/stories/{story_id}")
async def update_story(
    payload: StoryWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryRead]:
    """更新剧情元数据。"""
    data = await service.update(ctx.id, story_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}")
async def delete_story(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除剧情。"""
    await service.delete(ctx.id, story_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/chapters", status_code=status.HTTP_201_CREATED)
async def add_chapter(
    payload: StoryChapterWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryChapterRead]:
    """新增章节。"""
    data = await service.add_chapter(ctx.id, story_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/chapters/{chapter_id}")
async def delete_chapter(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    chapter_id: str = Depends(valid_story_chapter_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除章节。"""
    await service.delete_chapter(ctx.id, story_id, chapter_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_node(
    payload: StoryNodeWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryNodeRead]:
    """新增剧情节点。"""
    data = await service.add_node(ctx.id, story_id, payload)
    return ApiResponse(data=data)


@router.put("/stories/{story_id}/nodes/{node_id}")
async def update_node(
    payload: StoryNodeWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryNodeRead]:
    """更新剧情节点。"""
    data = await service.update_node(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}")
async def delete_node(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除剧情节点。"""
    await service.delete_node(ctx.id, story_id, node_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes/{node_id}/edges", status_code=status.HTTP_201_CREATED)
async def add_edge(
    payload: StoryEdgeWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryEdgeRead]:
    """连接下一节点。无条件环会被拒绝。"""
    data = await service.add_edge(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}/edges/{edge_id}")
async def delete_edge(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    edge_id: str = Depends(valid_story_edge_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除连线。"""
    await service.delete_edge(ctx.id, story_id, node_id, edge_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes/{node_id}/choices", status_code=status.HTTP_201_CREATED)
async def add_choice(
    payload: StoryChoiceWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryChoiceRead]:
    """为选项节点添加分支。"""
    data = await service.add_choice(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}/choices/{choice_id}")
async def delete_choice(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    choice_id: str = Depends(valid_story_choice_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除选项。"""
    await service.delete_choice(ctx.id, story_id, node_id, choice_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes/{node_id}/conditions", status_code=status.HTTP_201_CREATED)
async def add_condition(
    payload: StoryConditionWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryConditionRead]:
    """添加节点条件（不求值）。"""
    data = await service.add_condition(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}/conditions/{condition_id}")
async def delete_condition(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    condition_id: str = Depends(valid_story_condition_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除条件。"""
    await service.delete_condition(ctx.id, story_id, node_id, condition_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes/{node_id}/actions", status_code=status.HTTP_201_CREATED)
async def add_action(
    payload: StoryActionWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryActionRead]:
    """添加节点动作（不执行）。"""
    data = await service.add_action(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}/actions/{action_id}")
async def delete_action(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    action_id: str = Depends(valid_story_action_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """删除动作。"""
    await service.delete_action(ctx.id, story_id, node_id, action_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/stories/{story_id}/nodes/{node_id}/characters", status_code=status.HTTP_201_CREATED)
async def add_cast(
    payload: StoryCastWrite,
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[StoryCastRead]:
    """节点出场人物。"""
    data = await service.add_cast(ctx.id, story_id, node_id, payload)
    return ApiResponse(data=data)


@router.delete("/stories/{story_id}/nodes/{node_id}/characters/{cast_id}")
async def delete_cast(
    ctx: ProjectContext = Depends(get_project_context),
    story_id: str = Depends(valid_story_id),
    node_id: str = Depends(valid_story_node_id),
    cast_id: str = Depends(valid_story_cast_id),
    service: StoryService = Depends(get_story_service),
) -> ApiResponse[None]:
    """移除出场人物。"""
    await service.delete_cast(ctx.id, story_id, node_id, cast_id)
    return ApiResponse(data=None, meta={"deleted": True})
