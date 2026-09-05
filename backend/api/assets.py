"""资源 API。只登记元数据与相对路径，不渲染预览。"""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_character_id,
    valid_city_id,
    valid_map_id,
    valid_resource_id,
    valid_skill_id,
)
from backend.api.deps import get_asset_service
from backend.schemas.asset import (
    CharacterPresentationRead,
    CharacterPresentationWrite,
    ResourceBindWrite,
    ResourceRead,
    ResourceRef,
    ResourceWrite,
)
from backend.domain.asset_rules import ResourceType
from backend.schemas.common import ApiResponse
from backend.services.asset_service import AssetService

router = APIRouter(prefix="/projects/{project_id}", tags=["resources"])


@router.post("/resources", status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRead]:
    """登记资源。路径必须相对项目 assets 且文件存在。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.post("/resources/upload", status_code=status.HTTP_201_CREATED)
async def upload_resource(
    ctx: ProjectContext = Depends(get_project_context),
    file: UploadFile = File(...),
    code: str = Form(...),
    name: str = Form(...),
    resource_type: ResourceType = Form(...),
    path: str | None = Form(default=None),
    checksum: str | None = Form(default=None),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRead]:
    """上传二进制资源并写入项目 assets。"""
    content = await file.read()
    data = await service.upload(
        ctx.id,
        code=code,
        name=name,
        resource_type=resource_type,
        filename=file.filename or "unnamed.bin",
        content=content,
        path=path,
        checksum=checksum,
        mime_type=file.content_type,
    )
    return ApiResponse(data=data)


@router.get("/resources")
async def list_resources(
    ctx: ProjectContext = Depends(get_project_context),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[list[ResourceRead]]:
    """列出项目资源。"""
    data = await service.list_resources(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/resources/{resource_id}")
async def get_resource(
    ctx: ProjectContext = Depends(get_project_context),
    resource_id: str = Depends(valid_resource_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRead]:
    """获取资源并复查文件是否仍在。"""
    data = await service.get(ctx.id, resource_id)
    return ApiResponse(data=data)


@router.delete("/resources/{resource_id}")
async def delete_resource(
    ctx: ProjectContext = Depends(get_project_context),
    resource_id: str = Depends(valid_resource_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[None]:
    """删除资源登记。"""
    await service.delete(ctx.id, resource_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.put("/characters/{character_id}/presentation")
async def bind_character_presentation(
    payload: CharacterPresentationWrite,
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[CharacterPresentationRead]:
    """绑定人物头像与模型。只接受资源 ID，不接受裸路径。"""
    data = await service.bind_character_presentation(ctx.id, character_id, payload)
    return ApiResponse(data=data)


@router.put("/skills/{skill_id}/icon")
async def bind_skill_icon(
    payload: ResourceBindWrite,
    ctx: ProjectContext = Depends(get_project_context),
    skill_id: str = Depends(valid_skill_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRef | None]:
    """绑定技能图标。"""
    data = await service.bind_skill_icon(ctx.id, skill_id, payload.resource_id)
    return ApiResponse(data=data)


@router.put("/cities/{city_id}/icon")
async def bind_city_icon(
    payload: ResourceBindWrite,
    ctx: ProjectContext = Depends(get_project_context),
    city_id: str = Depends(valid_city_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRef | None]:
    """绑定城池图标。"""
    data = await service.bind_city_icon(ctx.id, city_id, payload.resource_id)
    return ApiResponse(data=data)


@router.put("/maps/{map_id}/preview")
async def bind_map_preview(
    payload: ResourceBindWrite,
    ctx: ProjectContext = Depends(get_project_context),
    map_id: str = Depends(valid_map_id),
    service: AssetService = Depends(get_asset_service),
) -> ApiResponse[ResourceRef | None]:
    """绑定地图预览图。"""
    data = await service.bind_map_preview(ctx.id, map_id, payload.resource_id)
    return ApiResponse(data=data)
