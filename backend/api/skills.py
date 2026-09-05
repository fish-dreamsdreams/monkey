"""技能定义与人物技能绑定 API。效果仅为数据，不结算战斗。"""

from fastapi import APIRouter, Depends, status

from backend.api.context import (
    ProjectContext,
    get_project_context,
    valid_character_id,
    valid_character_skill_id,
    valid_skill_id,
)
from backend.api.deps import get_skill_service
from backend.schemas.common import ApiResponse
from backend.schemas.skill import (
    CharacterSkillRead,
    CharacterSkillUpdate,
    CharacterSkillWrite,
    SkillRead,
    SkillWrite,
)
from backend.services.skill_service import SkillService

router = APIRouter(prefix="/projects/{project_id}", tags=["skills"])


@router.post("/skills", status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillWrite,
    ctx: ProjectContext = Depends(get_project_context),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[SkillRead]:
    """创建技能。effects 必须是可序列化数据，不能是脚本。"""
    data = await service.create(ctx.id, payload)
    return ApiResponse(data=data)


@router.get("/skills")
async def list_skills(
    ctx: ProjectContext = Depends(get_project_context),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[list[SkillRead]]:
    """列出项目技能目录。"""
    data = await service.list_skills(ctx.id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/skills/{skill_id}")
async def get_skill(
    ctx: ProjectContext = Depends(get_project_context),
    skill_id: str = Depends(valid_skill_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[SkillRead]:
    """获取技能定义。"""
    data = await service.get(ctx.id, skill_id)
    return ApiResponse(data=data)


@router.put("/skills/{skill_id}")
async def update_skill(
    payload: SkillWrite,
    ctx: ProjectContext = Depends(get_project_context),
    skill_id: str = Depends(valid_skill_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[SkillRead]:
    """更新技能定义。"""
    data = await service.update(ctx.id, skill_id, payload)
    return ApiResponse(data=data)


@router.delete("/skills/{skill_id}")
async def delete_skill(
    ctx: ProjectContext = Depends(get_project_context),
    skill_id: str = Depends(valid_skill_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[None]:
    """删除技能，并级联解除人物绑定。"""
    await service.delete(ctx.id, skill_id)
    return ApiResponse(data=None, meta={"deleted": True})


@router.post("/characters/{character_id}/skills", status_code=status.HTTP_201_CREATED)
async def bind_character_skill(
    payload: CharacterSkillWrite,
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[CharacterSkillRead]:
    """为人物绑定技能。不会写入 historical 史实栏。"""
    data = await service.bind(ctx.id, character_id, payload)
    return ApiResponse(data=data)


@router.get("/characters/{character_id}/skills")
async def list_character_skills(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[list[CharacterSkillRead]]:
    """列出人物技能。"""
    data = await service.list_character_skills(ctx.id, character_id)
    return ApiResponse(data=data, meta={"total": len(data)})


@router.put("/characters/{character_id}/skills/{binding_id}")
async def update_character_skill(
    payload: CharacterSkillUpdate,
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    binding_id: str = Depends(valid_character_skill_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[CharacterSkillRead]:
    """更新人物技能等级。"""
    data = await service.update_binding(ctx.id, character_id, binding_id, payload)
    return ApiResponse(data=data)


@router.delete("/characters/{character_id}/skills/{binding_id}")
async def unbind_character_skill(
    ctx: ProjectContext = Depends(get_project_context),
    character_id: str = Depends(valid_character_id),
    binding_id: str = Depends(valid_character_skill_id),
    service: SkillService = Depends(get_skill_service),
) -> ApiResponse[None]:
    """解除人物技能。"""
    await service.unbind(ctx.id, character_id, binding_id)
    return ApiResponse(data=None, meta={"deleted": True})
