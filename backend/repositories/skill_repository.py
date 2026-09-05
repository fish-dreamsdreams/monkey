"""技能与人物技能绑定仓储。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.skill import CharacterSkill, Skill


class SkillRepository:
    """技能目录与绑定持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, skill: Skill) -> Skill:
        """插入技能定义。"""
        self._session.add(skill)
        await self._session.flush()
        return skill

    async def get(self, project_id: str, skill_id: str) -> Skill | None:
        """按 ID 加载技能。"""
        result = await self._session.execute(
            select(Skill).where(Skill.project_id == project_id, Skill.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Skill | None:
        """按业务 code 加载技能。"""
        result = await self._session.execute(
            select(Skill).where(Skill.project_id == project_id, Skill.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[Skill]:
        """列出项目技能。"""
        result = await self._session.execute(
            select(Skill).where(Skill.project_id == project_id).order_by(Skill.skill_type, Skill.code)
        )
        return list(result.scalars().all())

    async def delete(self, skill: Skill) -> None:
        """删除技能（级联删除绑定）。"""
        await self._session.delete(skill)
        await self._session.flush()

    async def add_binding(self, binding: CharacterSkill) -> CharacterSkill:
        """插入人物技能绑定。"""
        self._session.add(binding)
        await self._session.flush()
        loaded = await self._session.execute(
            select(CharacterSkill)
            .options(selectinload(CharacterSkill.skill))
            .where(CharacterSkill.id == binding.id)
        )
        return loaded.scalar_one()

    async def get_binding(self, character_id: str, binding_id: str) -> CharacterSkill | None:
        """加载一条绑定。"""
        result = await self._session.execute(
            select(CharacterSkill)
            .options(selectinload(CharacterSkill.skill))
            .where(CharacterSkill.character_id == character_id, CharacterSkill.id == binding_id)
        )
        return result.scalar_one_or_none()

    async def get_binding_by_skill(self, character_id: str, skill_id: str) -> CharacterSkill | None:
        """同一人物是否已绑定该技能。"""
        result = await self._session.execute(
            select(CharacterSkill).where(
                CharacterSkill.character_id == character_id,
                CharacterSkill.skill_id == skill_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_bindings(self, character_id: str) -> list[CharacterSkill]:
        """列出人物已绑定技能。"""
        result = await self._session.execute(
            select(CharacterSkill)
            .options(selectinload(CharacterSkill.skill))
            .where(CharacterSkill.character_id == character_id)
            .order_by(CharacterSkill.id)
        )
        return list(result.scalars().all())

    async def delete_binding(self, binding: CharacterSkill) -> None:
        """解除绑定。"""
        await self._session.delete(binding)
        await self._session.flush()
