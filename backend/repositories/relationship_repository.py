"""人物关系仓储。"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.relationship import CharacterRelationship


class RelationshipRepository:
    """关系边持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _options(self) -> tuple[object, ...]:
        return (
            selectinload(CharacterRelationship.from_character),
            selectinload(CharacterRelationship.to_character),
        )

    async def add_many(self, rows: list[CharacterRelationship]) -> None:
        """插入一条或多条关系边。"""
        self._session.add_all(rows)
        await self._session.flush()

    async def get(self, project_id: str, relationship_id: str) -> CharacterRelationship | None:
        """按 ID 加载关系。"""
        result = await self._session.execute(
            select(CharacterRelationship)
            .options(*self._options())
            .where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.id == relationship_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_primary(self, project_id: str, character_id: str | None = None) -> list[CharacterRelationship]:
        """列出项目内用户创建的关系（不含对称反向边）。"""
        stmt = (
            select(CharacterRelationship)
            .options(*self._options())
            .where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.is_primary.is_(True),
            )
        )
        if character_id is not None:
            stmt = stmt.where(
                or_(
                    CharacterRelationship.from_character_id == character_id,
                    CharacterRelationship.to_character_id == character_id,
                )
            )
        stmt = stmt.order_by(CharacterRelationship.relationship_type, CharacterRelationship.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_character(self, project_id: str, character_id: str) -> list[CharacterRelationship]:
        """列出与某人物相关的全部有向边。"""
        result = await self._session.execute(
            select(CharacterRelationship)
            .options(*self._options())
            .where(
                CharacterRelationship.project_id == project_id,
                or_(
                    CharacterRelationship.from_character_id == character_id,
                    CharacterRelationship.to_character_id == character_id,
                ),
            )
            .order_by(CharacterRelationship.relationship_type, CharacterRelationship.id)
        )
        return list(result.scalars().all())

    async def list_same_type_between(
        self,
        project_id: str,
        left_id: str,
        right_id: str,
        relationship_type: str,
    ) -> list[CharacterRelationship]:
        """同一对人物、同一类型的已有边（含反向）。"""
        result = await self._session.execute(
            select(CharacterRelationship).where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.relationship_type == relationship_type,
                or_(
                    (CharacterRelationship.from_character_id == left_id)
                    & (CharacterRelationship.to_character_id == right_id),
                    (CharacterRelationship.from_character_id == right_id)
                    & (CharacterRelationship.to_character_id == left_id),
                ),
            )
        )
        return list(result.scalars().all())

    async def list_pair(self, project_id: str, pair_id: str) -> list[CharacterRelationship]:
        """一对对称关系的全部边。"""
        result = await self._session.execute(
            select(CharacterRelationship)
            .options(*self._options())
            .where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.pair_id == pair_id,
            )
        )
        return list(result.scalars().all())

    async def delete_pair(self, rows: list[CharacterRelationship]) -> None:
        """删除一对关系边。"""
        for row in rows:
            await self._session.delete(row)
        await self._session.flush()
