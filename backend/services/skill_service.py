"""技能应用服务。

职责：维护技能定义与人物绑定。效果只作为 JSON 数据读写，不调用任何战斗结算。
"""

from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.skill_rules import SkillTarget, SkillType
from backend.domain.source_types import SourceType
from backend.models.skill import CharacterSkill, Skill
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.skill_repository import SkillRepository
from backend.repositories.source_repository import SourceRepository
from backend.schemas.skill import (
    CharacterSkillRead,
    CharacterSkillUpdate,
    CharacterSkillWrite,
    SkillCost,
    SkillEffect,
    SkillHistoricalBasis,
    SkillRead,
    SkillTrigger,
    SkillWrite,
)


class SkillService:
    """技能用例编排。"""

    def __init__(
        self,
        skills: SkillRepository,
        characters: CharacterRepository,
        projects: ProjectRepository,
        sources: SourceRepository,
    ) -> None:
        self._skills = skills
        self._characters = characters
        self._projects = projects
        self._sources = sources

    async def create(self, project_id: str, payload: SkillWrite) -> SkillRead:
        """创建技能定义。"""
        await self._require_project(project_id)
        await self._validate_basis(project_id, payload.historical_basis)
        if await self._skills.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"技能 code 已存在: {payload.code}")
        skill = self._build_skill(project_id, new_id(EntityPrefix.SKILL), payload)
        await self._skills.add(skill)
        await self._bump(project_id)
        return self._to_skill_read(skill)

    async def get(self, project_id: str, skill_id: str) -> SkillRead:
        """获取技能定义。"""
        skill = await self._require_skill(project_id, skill_id)
        return self._to_skill_read(skill)

    async def list_skills(self, project_id: str) -> list[SkillRead]:
        """列出项目技能。"""
        await self._require_project(project_id)
        items = await self._skills.list_by_project(project_id)
        return [self._to_skill_read(item) for item in items]

    async def update(self, project_id: str, skill_id: str, payload: SkillWrite) -> SkillRead:
        """全量更新技能定义。仍不执行效果。"""
        skill = await self._require_skill(project_id, skill_id)
        await self._validate_basis(project_id, payload.historical_basis)
        duplicate = await self._skills.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != skill.id:
            raise ConflictError(f"技能 code 已存在: {payload.code}")
        self._apply_payload(skill, payload)
        await self._bump(project_id)
        return self._to_skill_read(skill)

    async def delete(self, project_id: str, skill_id: str) -> None:
        """删除技能及其人物绑定。"""
        skill = await self._require_skill(project_id, skill_id)
        await self._skills.delete(skill)
        await self._bump(project_id)

    async def bind(
        self,
        project_id: str,
        character_id: str,
        payload: CharacterSkillWrite,
    ) -> CharacterSkillRead:
        """把已有技能绑到人物。不改写人物史实栏。"""
        await self._require_character(project_id, character_id)
        skill_id = require_id(payload.skill_id, EntityPrefix.SKILL, field="skill_id")
        skill = await self._require_skill(project_id, skill_id)
        if await self._skills.get_binding_by_skill(character_id, skill.id) is not None:
            raise ConflictError("该人物已绑定此技能")
        binding = CharacterSkill(
            id=new_id(EntityPrefix.CHARACTER_SKILL),
            character_id=character_id,
            skill_id=skill.id,
            level=payload.level,
            source_note=payload.source_note,
        )
        saved = await self._skills.add_binding(binding)
        await self._bump(project_id)
        return self._to_binding_read(saved)

    async def list_character_skills(self, project_id: str, character_id: str) -> list[CharacterSkillRead]:
        """列出人物技能。"""
        await self._require_character(project_id, character_id)
        items = await self._skills.list_bindings(character_id)
        return [self._to_binding_read(item) for item in items]

    async def update_binding(
        self,
        project_id: str,
        character_id: str,
        binding_id: str,
        payload: CharacterSkillUpdate,
    ) -> CharacterSkillRead:
        """更新技能等级。"""
        await self._require_character(project_id, character_id)
        binding = await self._skills.get_binding(character_id, binding_id)
        if binding is None:
            raise NotFoundError("人物技能绑定不存在")
        binding.level = payload.level
        binding.source_note = payload.source_note
        await self._bump(project_id)
        loaded = await self._skills.get_binding(character_id, binding_id)
        if loaded is None:
            raise NotFoundError("人物技能绑定不存在")
        return self._to_binding_read(loaded)

    async def unbind(self, project_id: str, character_id: str, binding_id: str) -> None:
        """解除人物技能。"""
        await self._require_character(project_id, character_id)
        binding = await self._skills.get_binding(character_id, binding_id)
        if binding is None:
            raise NotFoundError("人物技能绑定不存在")
        await self._skills.delete_binding(binding)
        await self._bump(project_id)

    def _build_skill(self, project_id: str, skill_id: str, payload: SkillWrite) -> Skill:
        skill = Skill(id=skill_id, project_id=project_id)
        self._apply_payload(skill, payload)
        return skill

    def _apply_payload(self, skill: Skill, payload: SkillWrite) -> None:
        basis = payload.historical_basis
        skill.code = payload.code
        skill.name = payload.name.strip()
        skill.skill_type = payload.skill_type.value
        skill.description = payload.description
        skill.target = payload.target.value
        skill.cooldown = payload.cooldown
        skill.cost = payload.cost.model_dump(mode="json")
        skill.trigger_condition = (
            payload.trigger_condition.model_dump(mode="json") if payload.trigger_condition else None
        )
        skill.effects = [item.model_dump(mode="json") for item in payload.effects]
        skill.basis_source_type = basis.source_type.value if basis and basis.source_type else None
        skill.basis_source_code = basis.source_code if basis else None
        skill.basis_note = basis.note if basis else None

    def _to_skill_read(self, skill: Skill) -> SkillRead:
        basis = None
        if skill.basis_source_type or skill.basis_source_code or skill.basis_note:
            basis = SkillHistoricalBasis(
                source_type=SourceType(skill.basis_source_type) if skill.basis_source_type else None,
                source_code=skill.basis_source_code,
                note=skill.basis_note,
            )
        trigger = SkillTrigger.model_validate(skill.trigger_condition) if skill.trigger_condition else None
        return SkillRead(
            id=skill.id,
            project_id=skill.project_id,
            code=skill.code,
            name=skill.name,
            skill_type=SkillType(skill.skill_type),
            description=skill.description,
            target=SkillTarget(skill.target),
            cooldown=skill.cooldown,
            cost=SkillCost.model_validate(skill.cost),
            trigger_condition=trigger,
            effects=[SkillEffect.model_validate(item) for item in skill.effects],
            historical_basis=basis,
        )

    def _to_binding_read(self, binding: CharacterSkill) -> CharacterSkillRead:
        return CharacterSkillRead(
            id=binding.id,
            character_id=binding.character_id,
            skill=self._to_skill_read(binding.skill),
            level=binding.level,
            source_note=binding.source_note,
        )

    async def _validate_basis(self, project_id: str, basis: SkillHistoricalBasis | None) -> None:
        if basis is None or not basis.source_code:
            return
        source = await self._sources.get_by_code(project_id, basis.source_code)
        if source is None:
            raise ValidationError(f"来源不存在: {basis.source_code}", field="historical_basis")
        if basis.source_type is not None and source.source_type != basis.source_type.value:
            raise ValidationError("技能史源类型必须与目录中的来源类型一致", field="historical_basis")

    async def _require_skill(self, project_id: str, skill_id: str) -> Skill:
        await self._require_project(project_id)
        skill = await self._skills.get(project_id, skill_id)
        if skill is None:
            raise NotFoundError("技能不存在")
        return skill

    async def _require_character(self, project_id: str, character_id: str) -> None:
        await self._require_project(project_id)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")

    async def _require_project(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
