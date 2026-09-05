"""势力、成员与领土仓储。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.faction import Faction, FactionMember, FactionTerritory


class FactionRepository:
    """势力及时序表持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _faction_options(self) -> tuple[object, ...]:
        return (
            selectinload(Faction.leader_character),
            selectinload(Faction.capital_city),
        )

    async def add(self, faction: Faction) -> Faction:
        """插入势力。"""
        self._session.add(faction)
        await self._session.flush()
        return faction

    async def get(self, project_id: str, faction_id: str) -> Faction | None:
        """按 ID 加载势力。"""
        result = await self._session.execute(
            select(Faction)
            .options(*self._faction_options())
            .where(Faction.project_id == project_id, Faction.id == faction_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Faction | None:
        """按业务 code 加载势力。"""
        result = await self._session.execute(
            select(Faction).where(Faction.project_id == project_id, Faction.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[Faction]:
        """列出项目势力。"""
        result = await self._session.execute(
            select(Faction)
            .options(*self._faction_options())
            .where(Faction.project_id == project_id)
            .order_by(Faction.name, Faction.code)
        )
        return list(result.scalars().all())

    async def delete(self, faction: Faction) -> None:
        """删除势力（级联成员与领土）。"""
        await self._session.delete(faction)
        await self._session.flush()

    async def add_member(self, member: FactionMember) -> FactionMember:
        """插入成员时段。"""
        self._session.add(member)
        await self._session.flush()
        loaded = await self._session.execute(
            select(FactionMember)
            .options(selectinload(FactionMember.character), selectinload(FactionMember.faction))
            .where(FactionMember.id == member.id)
        )
        return loaded.scalar_one()

    async def get_member(self, project_id: str, member_id: str) -> FactionMember | None:
        """加载成员记录。"""
        result = await self._session.execute(
            select(FactionMember)
            .options(selectinload(FactionMember.character), selectinload(FactionMember.faction))
            .where(FactionMember.project_id == project_id, FactionMember.id == member_id)
        )
        return result.scalar_one_or_none()

    async def list_members(self, faction_id: str) -> list[FactionMember]:
        """列出势力全部成员记录。"""
        result = await self._session.execute(
            select(FactionMember)
            .options(selectinload(FactionMember.character), selectinload(FactionMember.faction))
            .where(FactionMember.faction_id == faction_id)
            .order_by(FactionMember.start_year, FactionMember.id)
        )
        return list(result.scalars().all())

    async def list_members_for_character(self, project_id: str, character_id: str) -> list[FactionMember]:
        """列出人物全部入势记录。"""
        result = await self._session.execute(
            select(FactionMember).where(
                FactionMember.project_id == project_id,
                FactionMember.character_id == character_id,
            )
        )
        return list(result.scalars().all())

    async def list_all_members(self, project_id: str) -> list[FactionMember]:
        """列出项目全部成员记录。"""
        result = await self._session.execute(
            select(FactionMember)
            .options(selectinload(FactionMember.character), selectinload(FactionMember.faction))
            .where(FactionMember.project_id == project_id)
        )
        return list(result.scalars().all())

    async def delete_member(self, member: FactionMember) -> None:
        """删除成员记录。"""
        await self._session.delete(member)
        await self._session.flush()

    async def add_territory(self, territory: FactionTerritory) -> FactionTerritory:
        """插入领土时段。"""
        self._session.add(territory)
        await self._session.flush()
        loaded = await self._session.execute(
            select(FactionTerritory)
            .options(selectinload(FactionTerritory.city), selectinload(FactionTerritory.faction))
            .where(FactionTerritory.id == territory.id)
        )
        return loaded.scalar_one()

    async def get_territory(self, project_id: str, territory_id: str) -> FactionTerritory | None:
        """加载领土记录。"""
        result = await self._session.execute(
            select(FactionTerritory)
            .options(selectinload(FactionTerritory.city), selectinload(FactionTerritory.faction))
            .where(FactionTerritory.project_id == project_id, FactionTerritory.id == territory_id)
        )
        return result.scalar_one_or_none()

    async def list_territories(self, faction_id: str) -> list[FactionTerritory]:
        """列出势力全部领土记录。"""
        result = await self._session.execute(
            select(FactionTerritory)
            .options(selectinload(FactionTerritory.city), selectinload(FactionTerritory.faction))
            .where(FactionTerritory.faction_id == faction_id)
            .order_by(FactionTerritory.start_year, FactionTerritory.id)
        )
        return list(result.scalars().all())

    async def list_territories_for_city(self, project_id: str, city_id: str) -> list[FactionTerritory]:
        """列出城池全部归属记录。"""
        result = await self._session.execute(
            select(FactionTerritory)
            .options(selectinload(FactionTerritory.faction))
            .where(FactionTerritory.project_id == project_id, FactionTerritory.city_id == city_id)
        )
        return list(result.scalars().all())

    async def list_all_territories(self, project_id: str) -> list[FactionTerritory]:
        """列出项目全部领土记录。"""
        result = await self._session.execute(
            select(FactionTerritory)
            .options(selectinload(FactionTerritory.city), selectinload(FactionTerritory.faction))
            .where(FactionTerritory.project_id == project_id)
        )
        return list(result.scalars().all())

    async def delete_territory(self, territory: FactionTerritory) -> None:
        """删除领土记录。"""
        await self._session.delete(territory)
        await self._session.flush()
