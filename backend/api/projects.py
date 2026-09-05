"""项目与性格标签 API。"""

from fastapi import APIRouter, Depends, status

from backend.api.context import ProjectContext, get_project_context, valid_personality_tag_id
from backend.api.deps import get_project_service
from backend.schemas.character import PersonalityTagRead
from backend.schemas.common import ApiResponse
from backend.schemas.personality import PersonalityTagCreate, PersonalityTagUpdate
from backend.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectRead]:
    """创建内容项目，并写入系统性格标签。"""
    data = await service.create(payload)
    return ApiResponse(data=data)


@router.get("")
async def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[list[ProjectRead]]:
    """列出全部项目。"""
    data = await service.list_projects()
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/{project_id}")
async def get_project(
    ctx: ProjectContext = Depends(get_project_context),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectRead]:
    """获取项目详情。先解析项目上下文。"""
    data = await service.get(ctx.id)
    return ApiResponse(data=data)


@router.put("/{project_id}")
async def update_project(
    payload: ProjectUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectRead]:
    """更新项目名称、描述与目标年代。code 不可改。"""
    data = await service.update(ctx.id, payload)
    return ApiResponse(data=data)


@router.delete("/{project_id}")
async def delete_project(
    ctx: ProjectContext = Depends(get_project_context),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[None]:
    """删除项目及工作区文件。"""
    await service.delete(ctx.id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.get("/{project_id}/personality-tags")
async def list_personality_tags(
    ctx: ProjectContext = Depends(get_project_context),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[list[PersonalityTagRead]]:
    """列出项目性格标签。"""
    tags = await service.list_personality_tags(ctx.id)
    data = [PersonalityTagRead.model_validate(tag) for tag in tags]
    return ApiResponse(data=data, meta={"total": len(data)})


@router.post("/{project_id}/personality-tags", status_code=status.HTTP_201_CREATED)
async def create_personality_tag(
    payload: PersonalityTagCreate,
    ctx: ProjectContext = Depends(get_project_context),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[PersonalityTagRead]:
    """新增自定义性格标签。"""
    tag = await service.create_personality_tag(ctx.id, payload)
    return ApiResponse(data=PersonalityTagRead.model_validate(tag))


@router.put("/{project_id}/personality-tags/{tag_id}")
async def update_personality_tag(
    payload: PersonalityTagUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    tag_id: str = Depends(valid_personality_tag_id),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[PersonalityTagRead]:
    """更新性格标签名称与说明。"""
    tag = await service.update_personality_tag(ctx.id, tag_id, payload)
    return ApiResponse(data=PersonalityTagRead.model_validate(tag))


@router.delete("/{project_id}/personality-tags/{tag_id}")
async def delete_personality_tag(
    ctx: ProjectContext = Depends(get_project_context),
    tag_id: str = Depends(valid_personality_tag_id),
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[None]:
    """删除自定义性格标签。"""
    await service.delete_personality_tag(ctx.id, tag_id)
    return ApiResponse(data=None, meta={"deleted": True})
