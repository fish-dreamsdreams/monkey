"""历史事件应用服务。

职责：维护编年事件与参与关系。更新年份时重新校验生卒与存续。不执行后果。
"""

from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.event_rules import (
    EventFactionRole,
    EventParticipantRole,
    EventType,
    validate_character_alive_in_year,
    validate_city_exists_in_year,
    validate_event_date,
    validate_faction_exists_in_year,
)
from backend.domain.source_types import BoundLayer, SourceType, is_fact_eligible, validate_citation_layer
from backend.models.event import EventFaction, EventParticipant, EventSource, HistoricalEvent
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.event_repository import EventRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.source_repository import SourceRepository
from backend.schemas.city import CityRef, FactionRef
from backend.schemas.event import (
    EventFactionRead,
    EventFactionWrite,
    EventParticipantRead,
    EventParticipantWrite,
    EventRead,
    EventSourceRead,
    EventSourceWrite,
    EventSummary,
    EventWrite,
)
from backend.schemas.relationship import CharacterRef


class EventService:
    """历史事件用例编排。"""

    def __init__(
        self,
        events: EventRepository,
        characters: CharacterRepository,
        cities: CityRepository,
        factions: FactionRepository,
        sources: SourceRepository,
        projects: ProjectRepository,
    ) -> None:
        self._events = events
        self._characters = characters
        self._cities = cities
        self._factions = factions
        self._sources = sources
        self._projects = projects

    async def create(self, project_id: str, payload: EventWrite) -> EventRead:
        """创建事件正文。"""
        await self._require_project(project_id)
        validate_event_date(payload.year, payload.month, payload.day)
        if await self._events.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"事件 code 已存在: {payload.code}")
        await self._validate_location(project_id, payload)
        event = HistoricalEvent(id=new_id(EntityPrefix.EVENT), project_id=project_id)
        self._apply(event, payload)
        await self._events.add(event)
        await self._bump(project_id)
        loaded = await self._require_event(project_id, event.id)
        return self._to_read(loaded)

    async def get(self, project_id: str, event_id: str) -> EventRead:
        """获取事件。"""
        return self._to_read(await self._require_event(project_id, event_id))

    async def list_events(
        self,
        project_id: str,
        year: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list[EventSummary]:
        """列出事件。"""
        await self._require_project(project_id)
        items = await self._events.list_by_project(
            project_id, year=year, from_year=from_year, to_year=to_year
        )
        return [self._to_summary(item) for item in items]

    async def update(self, project_id: str, event_id: str, payload: EventWrite) -> EventRead:
        """更新事件。年份变化时重验全部参与者与势力。"""
        event = await self._require_event(project_id, event_id)
        validate_event_date(payload.year, payload.month, payload.day)
        duplicate = await self._events.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != event.id:
            raise ConflictError(f"事件 code 已存在: {payload.code}")
        await self._validate_location(project_id, payload)
        self._apply(event, payload)
        await self._revalidate_links(project_id, event)
        await self._bump(project_id)
        loaded = await self._require_event(project_id, event.id)
        return self._to_read(loaded)

    async def delete(self, project_id: str, event_id: str) -> None:
        """删除事件。"""
        event = await self._require_event(project_id, event_id)
        await self._events.delete(event)
        await self._bump(project_id)

    async def add_participant(
        self, project_id: str, event_id: str, payload: EventParticipantWrite
    ) -> EventParticipantRead:
        """人物参与事件，必须活在事件当年。"""
        event = await self._require_event(project_id, event_id)
        character_id = require_id(payload.character_id, EntityPrefix.CHARACTER, field="character_id")
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        if await self._events.get_participant_by_character(event.id, character.id) is not None:
            raise ConflictError("该人物已参与此事件")
        validate_character_alive_in_year(
            character_name=character.name,
            birth_year=character.birth_year,
            death_year=character.death_year,
            event_year=event.year,
        )
        saved = await self._events.add_participant(
            EventParticipant(
                id=new_id(EntityPrefix.EVENT_PARTICIPANT),
                event_id=event.id,
                character_id=character.id,
                role=payload.role.value,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_participant_read(saved)

    async def delete_participant(self, project_id: str, event_id: str, participant_id: str) -> None:
        """移除参与者。"""
        await self._require_event(project_id, event_id)
        participant = await self._events.get_participant(event_id, participant_id)
        if participant is None:
            raise NotFoundError("事件参与记录不存在")
        await self._events.delete_participant(participant)
        await self._bump(project_id)

    async def add_faction(
        self, project_id: str, event_id: str, payload: EventFactionWrite
    ) -> EventFactionRead:
        """势力牵涉事件，必须在事件年存续。"""
        event = await self._require_event(project_id, event_id)
        faction_id = require_id(payload.faction_id, EntityPrefix.FACTION, field="faction_id")
        faction = await self._factions.get(project_id, faction_id)
        if faction is None:
            raise NotFoundError("势力不存在")
        if await self._events.get_faction_link_by_faction(event.id, faction.id) is not None:
            raise ConflictError("该势力已牵涉此事件")
        validate_faction_exists_in_year(
            faction_name=faction.name,
            start_year=faction.start_year,
            end_year=faction.end_year,
            event_year=event.year,
        )
        saved = await self._events.add_faction(
            EventFaction(
                id=new_id(EntityPrefix.EVENT_FACTION),
                event_id=event.id,
                faction_id=faction.id,
                role=payload.role.value,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_faction_read(saved)

    async def delete_faction(self, project_id: str, event_id: str, link_id: str) -> None:
        """移除势力牵涉。"""
        await self._require_event(project_id, event_id)
        link = await self._events.get_faction_link(event_id, link_id)
        if link is None:
            raise NotFoundError("事件势力记录不存在")
        await self._events.delete_faction_link(link)
        await self._bump(project_id)

    async def add_source(self, project_id: str, event_id: str, payload: EventSourceWrite) -> EventSourceRead:
        """为事件挂史源。史实层不能引用演义。"""
        event = await self._require_event(project_id, event_id)
        source = await self._sources.get_by_code(project_id, payload.source_code)
        if source is None:
            raise NotFoundError("史料不存在")
        if await self._events.get_source_by_source_id(event.id, source.id) is not None:
            raise ConflictError("该史料已引用于此事件")
        validate_citation_layer(SourceType(source.source_type), BoundLayer(event.layer))
        saved = await self._events.add_source(
            EventSource(
                id=new_id(EntityPrefix.EVENT_SOURCE),
                event_id=event.id,
                source_id=source.id,
                quotation=payload.quotation,
                reference=payload.reference,
                note=payload.note,
            )
        )
        await self._bump(project_id)
        return self._to_source_read(saved)

    async def delete_source(self, project_id: str, event_id: str, citation_id: str) -> None:
        """移除事件引文。"""
        await self._require_event(project_id, event_id)
        citation = await self._events.get_source(event_id, citation_id)
        if citation is None:
            raise NotFoundError("事件引文不存在")
        await self._events.delete_source(citation)
        await self._bump(project_id)

    def _apply(self, event: HistoricalEvent, payload: EventWrite) -> None:
        event.code = payload.code
        event.name = payload.name
        event.event_type = payload.event_type.value
        event.layer = payload.layer.value
        event.year = payload.year
        event.month = payload.month
        event.day = payload.day
        event.location_city_id = payload.location_city_id
        event.location_note = payload.location_note
        event.description = payload.description
        event.consequences = payload.consequences

    async def _validate_location(self, project_id: str, payload: EventWrite) -> None:
        if payload.location_city_id is None:
            return
        city_id = require_id(payload.location_city_id, EntityPrefix.CITY, field="location_city_id")
        city = await self._cities.get(project_id, city_id)
        if city is None:
            raise NotFoundError("城池不存在")
        validate_city_exists_in_year(
            city_name=city.name,
            founded_year=city.founded_year,
            destroyed_year=city.destroyed_year,
            event_year=payload.year,
        )

    async def _revalidate_links(self, project_id: str, event: HistoricalEvent) -> None:
        for participant in event.participants:
            character = participant.character
            validate_character_alive_in_year(
                character_name=character.name,
                birth_year=character.birth_year,
                death_year=character.death_year,
                event_year=event.year,
            )
        for link in event.factions:
            faction = link.faction
            validate_faction_exists_in_year(
                faction_name=faction.name,
                start_year=faction.start_year,
                end_year=faction.end_year,
                event_year=event.year,
            )
        if event.location_city is not None:
            city = event.location_city
            validate_city_exists_in_year(
                city_name=city.name,
                founded_year=city.founded_year,
                destroyed_year=city.destroyed_year,
                event_year=event.year,
            )
        layer = BoundLayer(event.layer)
        for citation in event.sources:
            validate_citation_layer(SourceType(citation.source.source_type), layer)

    def _to_read(self, event: HistoricalEvent) -> EventRead:
        return EventRead(
            id=event.id,
            project_id=event.project_id,
            code=event.code,
            name=event.name,
            event_type=EventType(event.event_type),
            layer=BoundLayer(event.layer),
            year=event.year,
            month=event.month,
            day=event.day,
            location=self._city_ref(event.location_city),
            location_note=event.location_note,
            description=event.description,
            consequences=event.consequences,
            participants=[self._to_participant_read(item) for item in event.participants],
            factions=[self._to_faction_read(item) for item in event.factions],
            sources=[self._to_source_read(item) for item in event.sources],
        )

    def _to_summary(self, event: HistoricalEvent) -> EventSummary:
        return EventSummary(
            id=event.id,
            project_id=event.project_id,
            code=event.code,
            name=event.name,
            event_type=EventType(event.event_type),
            layer=BoundLayer(event.layer),
            year=event.year,
            month=event.month,
            day=event.day,
            location=self._city_ref(event.location_city),
            participant_count=len(event.participants) if event.participants is not None else 0,
            faction_count=len(event.factions) if event.factions is not None else 0,
        )

    def _city_ref(self, city) -> CityRef | None:
        if city is None:
            return None
        return CityRef(id=city.id, code=city.code, name=city.name)

    def _to_participant_read(self, item: EventParticipant) -> EventParticipantRead:
        return EventParticipantRead(
            id=item.id,
            character=CharacterRef(id=item.character.id, code=item.character.code, name=item.character.name),
            role=EventParticipantRole(item.role),
            note=item.note,
        )

    def _to_faction_read(self, item: EventFaction) -> EventFactionRead:
        faction = item.faction
        return EventFactionRead(
            id=item.id,
            faction=FactionRef(id=faction.id, code=faction.code, name=faction.name, color=faction.color),
            role=EventFactionRole(item.role),
            note=item.note,
        )

    def _to_source_read(self, item: EventSource) -> EventSourceRead:
        source_type = SourceType(item.source.source_type)
        return EventSourceRead(
            id=item.id,
            source_id=item.source.id,
            source_code=item.source.code,
            source_name=item.source.name,
            source_type=source_type,
            quotation=item.quotation,
            reference=item.reference,
            note=item.note,
            fact_eligible=is_fact_eligible(source_type),
        )

    async def _require_event(self, project_id: str, event_id: str) -> HistoricalEvent:
        event = await self._events.get(project_id, event_id)
        if event is None:
            raise NotFoundError("事件不存在")
        return event

    async def _require_project(self, project_id: str):
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
