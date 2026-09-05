"""项目与性格标签 API。"""

from fastapi import APIRouter, Depends, status

from backend.api.deps import get_project_service
from backend.schemas.character import PersonalityTagRead
from backend.schemas.common import ApiResponse
from backend.schemas.personality import PersonalityTagCreate
from backend.schemas.project import ProjectCreate, ProjectRead
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
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectRead]:
    """获取项目详情。"""
    data = await service.get(project_id)
    return ApiResponse(data=data)


@router.get("/{project_id}/personality-tags")
async def list_personality_tags(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[list[PersonalityTagRead]]:
    """列出项目性格标签。"""
    tags = await service.list_personality_tags(project_id)
    data = [PersonalityTagRead.model_validate(tag) for tag in tags]
    return ApiResponse(data=data, meta={"total": len(data)})


@router.post("/{project_id}/personality-tags", status_code=status.HTTP_201_CREATED)
async def create_personality_tag(
    project_id: str,
    payload: PersonalityTagCreate,
    service: ProjectService = Depends(get_project_service),
) -> ApiResponse[PersonalityTagRead]:
    """新增自定义性格标签。"""
    tag = await service.create_personality_tag(project_id, payload)
    return ApiResponse(data=PersonalityTagRead.model_validate(tag))
