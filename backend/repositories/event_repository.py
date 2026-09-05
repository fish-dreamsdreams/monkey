"""历史事件仓储。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.event import EventFaction, EventParticipant, EventSource, HistoricalEvent


class EventRepository:
    """事件及关联表持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _detail_options(self) -> tuple[object, ...]:
        return (
            selectinload(HistoricalEvent.location_city),
            selectinload(HistoricalEvent.participants).selectinload(EventParticipant.character),
            selectinload(HistoricalEvent.factions).selectinload(EventFaction.faction),
            selectinload(HistoricalEvent.sources).selectinload(EventSource.source),
        )

    async def add(self, event: HistoricalEvent) -> HistoricalEvent:
        """插入事件。"""
        self._session.add(event)
        await self._session.flush()
        return event

    async def get(self, project_id: str, event_id: str) -> HistoricalEvent | None:
        """按 ID 加载事件聚合。"""
        result = await self._session.execute(
            select(HistoricalEvent)
            .options(*self._detail_options())
            .where(HistoricalEvent.project_id == project_id, HistoricalEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> HistoricalEvent | None:
        """按业务 code 加载事件。"""
        result = await self._session.execute(
            select(HistoricalEvent).where(
                HistoricalEvent.project_id == project_id,
                HistoricalEvent.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_validation(self, project_id: str) -> list[HistoricalEvent]:
        """加载事件聚合，供跨实体校验。"""
        result = await self._session.execute(
            select(HistoricalEvent)
            .options(*self._detail_options())
            .where(HistoricalEvent.project_id == project_id)
            .order_by(HistoricalEvent.year, HistoricalEvent.code)
        )
        return list(result.scalars().all())

    async def list_by_project(
        self,
        project_id: str,
        year: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list[HistoricalEvent]:
        """列出项目事件，可按年份过滤。"""
        stmt = (
            select(HistoricalEvent)
            .options(
                selectinload(HistoricalEvent.location_city),
                selectinload(HistoricalEvent.participants),
                selectinload(HistoricalEvent.factions),
            )
            .where(HistoricalEvent.project_id == project_id)
        )
        if year is not None:
            stmt = stmt.where(HistoricalEvent.year == year)
        if from_year is not None:
            stmt = stmt.where(HistoricalEvent.year >= from_year)
        if to_year is not None:
            stmt = stmt.where(HistoricalEvent.year <= to_year)
        stmt = stmt.order_by(
            HistoricalEvent.year,
            HistoricalEvent.month,
            HistoricalEvent.day,
            HistoricalEvent.name,
            HistoricalEvent.code,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, event: HistoricalEvent) -> None:
        """删除事件（级联参与者、势力与引文）。"""
        await self._session.delete(event)
        await self._session.flush()

    async def add_participant(self, participant: EventParticipant) -> EventParticipant:
        """插入参与者。"""
        self._session.add(participant)
        await self._session.flush()
        loaded = await self._session.execute(
            select(EventParticipant)
            .options(selectinload(EventParticipant.character), selectinload(EventParticipant.event))
            .where(EventParticipant.id == participant.id)
        )
        return loaded.scalar_one()

    async def get_participant(self, event_id: str, participant_id: str) -> EventParticipant | None:
        """加载参与记录。"""
        result = await self._session.execute(
            select(EventParticipant).where(
                EventParticipant.event_id == event_id,
                EventParticipant.id == participant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_participant_by_character(self, event_id: str, character_id: str) -> EventParticipant | None:
        """按人物查找参与记录。"""
        result = await self._session.execute(
            select(EventParticipant).where(
                EventParticipant.event_id == event_id,
                EventParticipant.character_id == character_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_participant(self, participant: EventParticipant) -> None:
        """删除参与记录。"""
        await self._session.delete(participant)
        await self._session.flush()

    async def add_faction(self, link: EventFaction) -> EventFaction:
        """插入势力牵涉。"""
        self._session.add(link)
        await self._session.flush()
        loaded = await self._session.execute(
            select(EventFaction)
            .options(selectinload(EventFaction.faction), selectinload(EventFaction.event))
            .where(EventFaction.id == link.id)
        )
        return loaded.scalar_one()

    async def get_faction_link(self, event_id: str, link_id: str) -> EventFaction | None:
        """加载势力牵涉。"""
        result = await self._session.execute(
            select(EventFaction).where(EventFaction.event_id == event_id, EventFaction.id == link_id)
        )
        return result.scalar_one_or_none()

    async def get_faction_link_by_faction(self, event_id: str, faction_id: str) -> EventFaction | None:
        """按势力查找牵涉记录。"""
        result = await self._session.execute(
            select(EventFaction).where(
                EventFaction.event_id == event_id,
                EventFaction.faction_id == faction_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_faction_link(self, link: EventFaction) -> None:
        """删除势力牵涉。"""
        await self._session.delete(link)
        await self._session.flush()

    async def add_source(self, citation: EventSource) -> EventSource:
        """插入事件引文。"""
        self._session.add(citation)
        await self._session.flush()
        loaded = await self._session.execute(
            select(EventSource)
            .options(selectinload(EventSource.source), selectinload(EventSource.event))
            .where(EventSource.id == citation.id)
        )
        return loaded.scalar_one()

    async def get_source(self, event_id: str, citation_id: str) -> EventSource | None:
        """加载事件引文。"""
        result = await self._session.execute(
            select(EventSource).where(EventSource.event_id == event_id, EventSource.id == citation_id)
        )
        return result.scalar_one_or_none()

    async def get_source_by_source_id(self, event_id: str, source_id: str) -> EventSource | None:
        """按史料查找引文。"""
        result = await self._session.execute(
            select(EventSource).where(EventSource.event_id == event_id, EventSource.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def delete_source(self, citation: EventSource) -> None:
        """删除事件引文。"""
        await self._session.delete(citation)
        await self._session.flush()
