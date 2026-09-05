"""人物仓储。

职责：人物聚合根的加载与保存，装配历史记录、游戏属性与性格绑定。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.character import Character
from backend.models.personality import CharacterPersonality
from backend.models.source import CharacterSource


class CharacterRepository:
    """人物持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _detail_options(self) -> tuple[object, ...]:
        return (
            selectinload(Character.historical_record),
            selectinload(Character.attributes),
            selectinload(Character.personalities).selectinload(CharacterPersonality.tag),
            selectinload(Character.citations).selectinload(CharacterSource.source),
        )

    async def add(self, character: Character) -> Character:
        """插入人物聚合。"""
        self._session.add(character)
        await self._session.flush()
        return character

    async def get(self, project_id: str, character_id: str) -> Character | None:
        """按项目与人物 ID 加载完整聚合。"""
        result = await self._session.execute(
            select(Character)
            .options(*self._detail_options())
            .where(Character.project_id == project_id, Character.id == character_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Character | None:
        """按业务 code 查询人物。"""
        result = await self._session.execute(
            select(Character).where(Character.project_id == project_id, Character.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str, skip: int, limit: int) -> tuple[list[Character], int]:
        """分页列出项目内人物。"""
        total_result = await self._session.execute(
            select(func.count()).select_from(Character).where(Character.project_id == project_id)
        )
        total = int(total_result.scalar_one())
        result = await self._session.execute(
            select(Character)
            .where(Character.project_id == project_id)
            .order_by(Character.name, Character.code)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def delete(self, character: Character) -> None:
        """删除人物（级联删除历史、属性、性格绑定）。"""
        await self._session.delete(character)
        await self._session.flush()

    async def flush(self) -> None:
        """刷新会话，使集合替换等中间状态写入数据库。"""
        await self._session.flush()
