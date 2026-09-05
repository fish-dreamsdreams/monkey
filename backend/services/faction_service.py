"""势力应用服务。

职责：用户创建势力，并用时序表记录人物入势与城池归属。不内置魏蜀吴。
"""

from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.faction_rules import (
    FactionMemberRole,
    assert_no_overlap,
    validate_interval_within,
)
from backend.domain.year_range import contains_year, validate_year_range
from backend.models.faction import Faction, FactionMember, FactionTerritory
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.city import CityRef, FactionRef
from backend.schemas.faction import (
    FactionMemberRead,
    FactionMemberWrite,
    FactionRead,
    FactionTerritoryRead,
    FactionTerritoryWrite,
    FactionWrite,
    FactionYearRead,
    YearView,
)
from backend.schemas.relationship import CharacterRef
from backend.services.city_service import CityService


class FactionService:
    """势力与时序归属用例。"""

    def __init__(
        self,
        factions: FactionRepository,
        cities: CityRepository,
        characters: CharacterRepository,
        projects: ProjectRepository,
        city_service: CityService,
    ) -> None:
        self._factions = factions
        self._cities = cities
        self._characters = characters
        self._projects = projects
        self._city_service = city_service

    async def create(self, project_id: str, payload: FactionWrite) -> FactionRead:
        """创建势力。"""
        await self._require_project(project_id)
        validate_year_range(payload.start_year, payload.end_year, message="势力起始年份不能晚于结束年份")
        if await self._factions.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"势力 code 已存在: {payload.code}")
        await self._validate_pointers(project_id, payload)
        faction = Faction(id=new_id(EntityPrefix.FACTION), project_id=project_id)
        self._apply(faction, payload)
        await self._factions.add(faction)
        await self._bump(project_id)
        loaded = await self._require_faction(project_id, faction.id)
        return self._to_faction_read(loaded)

    async def get(self, project_id: str, faction_id: str) -> FactionRead:
        """获取势力。"""
        return self._to_faction_read(await self._require_faction(project_id, faction_id))

    async def list_factions(self, project_id: str) -> list[FactionRead]:
        """列出项目势力。"""
        await self._require_project(project_id)
        return [self._to_faction_read(item) for item in await self._factions.list_by_project(project_id)]

    async def update(self, project_id: str, faction_id: str, payload: FactionWrite) -> FactionRead:
        """更新势力。"""
        faction = await self._require_faction(project_id, faction_id)
        validate_year_range(payload.start_year, payload.end_year, message="势力起始年份不能晚于结束年份")
        duplicate = await self._factions.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != faction.id:
            raise ConflictError(f"势力 code 已存在: {payload.code}")
        await self._validate_pointers(project_id, payload)
        self._apply(faction, payload)
        await self._bump(project_id)
        loaded = await self._require_faction(project_id, faction.id)
        return self._to_faction_read(loaded)

    async def delete(self, project_id: str, faction_id: str) -> None:
        """删除势力及其成员、领土。"""
        faction = await self._require_faction(project_id, faction_id)
        await self._factions.delete(faction)
        await self._bump(project_id)

    async def add_member(self, project_id: str, faction_id: str, payload: FactionMemberWrite) -> FactionMemberRead:
        """人物在某时段加入势力。同一时段不能同时属于两个势力。"""
        faction = await self._require_faction(project_id, faction_id)
        validate_year_range(payload.start_year, payload.end_year, message="入势起始年份不能晚于结束年份")
        character_id = require_id(payload.character_id, EntityPrefix.CHARACTER, field="character_id")
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        validate_interval_within(
            inner_start=payload.start_year,
            inner_end=payload.end_year,
            outer_start=character.birth_year,
            outer_end=character.death_year,
            field="start_year",
            message="入势时段必须落在人物生卒年之内",
        )
        validate_interval_within(
            inner_start=payload.start_year,
            inner_end=payload.end_year,
            outer_start=faction.start_year,
            outer_end=faction.end_year,
            field="start_year",
            message="入势时段必须落在势力存续年之内",
        )
        existing = await self._factions.list_members_for_character(project_id, character.id)
        assert_no_overlap(
            [(item.start_year, item.end_year) for item in existing],
            payload.start_year,
            payload.end_year,
            "该人物在此时段已属于其他势力或已有重叠入势记录",
        )
        member = FactionMember(
            id=new_id(EntityPrefix.FACTION_MEMBER),
            project_id=project_id,
            faction_id=faction.id,
            character_id=character.id,
            role=payload.role.value,
            start_year=payload.start_year,
            end_year=payload.end_year,
            note=payload.note,
        )
        saved = await self._factions.add_member(member)
        await self._bump(project_id)
        return self._to_member_read(saved)

    async def list_members(self, project_id: str, faction_id: str) -> list[FactionMemberRead]:
        """列出势力成员记录。"""
        await self._require_faction(project_id, faction_id)
        return [self._to_member_read(item) for item in await self._factions.list_members(faction_id)]

    async def delete_member(self, project_id: str, faction_id: str, member_id: str) -> None:
        """删除入势记录。"""
        await self._require_faction(project_id, faction_id)
        member = await self._factions.get_member(project_id, member_id)
        if member is None or member.faction_id != faction_id:
            raise NotFoundError("势力成员记录不存在")
        await self._factions.delete_member(member)
        await self._bump(project_id)

    async def add_territory(
        self, project_id: str, faction_id: str, payload: FactionTerritoryWrite
    ) -> FactionTerritoryRead:
        """城池在某时段归属该势力。同一时段不能两属。"""
        faction = await self._require_faction(project_id, faction_id)
        validate_year_range(payload.start_year, payload.end_year, message="领土起始年份不能晚于结束年份")
        city_id = require_id(payload.city_id, EntityPrefix.CITY, field="city_id")
        city = await self._cities.get(project_id, city_id)
        if city is None:
            raise NotFoundError("城池不存在")
        validate_interval_within(
            inner_start=payload.start_year,
            inner_end=payload.end_year,
            outer_start=city.founded_year,
            outer_end=city.destroyed_year,
            field="start_year",
            message="领土时段必须落在城池存续年之内",
        )
        validate_interval_within(
            inner_start=payload.start_year,
            inner_end=payload.end_year,
            outer_start=faction.start_year,
            outer_end=faction.end_year,
            field="start_year",
            message="领土时段必须落在势力存续年之内",
        )
        existing = await self._factions.list_territories_for_city(project_id, city.id)
        assert_no_overlap(
            [(item.start_year, item.end_year) for item in existing],
            payload.start_year,
            payload.end_year,
            "该城池在此时段已归属其他势力或已有重叠领土记录",
        )
        territory = FactionTerritory(
            id=new_id(EntityPrefix.FACTION_TERRITORY),
            project_id=project_id,
            faction_id=faction.id,
            city_id=city.id,
            start_year=payload.start_year,
            end_year=payload.end_year,
            note=payload.note,
        )
        saved = await self._factions.add_territory(territory)
        await self._bump(project_id)
        return self._to_territory_read(saved)

    async def list_territories(self, project_id: str, faction_id: str) -> list[FactionTerritoryRead]:
        """列出势力领土记录。"""
        await self._require_faction(project_id, faction_id)
        return [self._to_territory_read(item) for item in await self._factions.list_territories(faction_id)]

    async def delete_territory(self, project_id: str, faction_id: str, territory_id: str) -> None:
        """删除领土记录。"""
        await self._require_faction(project_id, faction_id)
        territory = await self._factions.get_territory(project_id, territory_id)
        if territory is None or territory.faction_id != faction_id:
            raise NotFoundError("领土记录不存在")
        await self._factions.delete_territory(territory)
        await self._bump(project_id)

    async def year_view(self, project_id: str, year: int) -> YearView:
        """按年份派生世界视图：城池归属与在势成员。"""
        await self._require_project(project_id)
        cities = await self._city_service.list_cities(project_id, at_year=year)
        factions = await self._factions.list_by_project(project_id)
        members = await self._factions.list_all_members(project_id)
        territories = await self._factions.list_all_territories(project_id)
        faction_views: list[FactionYearRead] = []
        for faction in factions:
            if not contains_year(faction.start_year, faction.end_year, year):
                continue
            year_members = [
                self._to_member_read(item)
                for item in members
                if item.faction_id == faction.id and contains_year(item.start_year, item.end_year, year)
            ]
            year_cities = [
                CityRef(id=item.city.id, code=item.city.code, name=item.city.name)
                for item in territories
                if item.faction_id == faction.id and contains_year(item.start_year, item.end_year, year)
            ]
            base = self._to_faction_read(faction)
            faction_views.append(
                FactionYearRead(
                    **base.model_dump(),
                    members=year_members,
                    cities=year_cities,
                )
            )
        return YearView(year=year, cities=cities, factions=faction_views)

    def _apply(self, faction: Faction, payload: FactionWrite) -> None:
        faction.code = payload.code
        faction.name = payload.name
        faction.color = payload.color
        faction.leader_character_id = payload.leader_character_id
        faction.capital_city_id = payload.capital_city_id
        faction.start_year = payload.start_year
        faction.end_year = payload.end_year
        faction.historical_description = payload.historical_description

    async def _validate_pointers(self, project_id: str, payload: FactionWrite) -> None:
        if payload.leader_character_id is not None:
            leader_id = require_id(
                payload.leader_character_id, EntityPrefix.CHARACTER, field="leader_character_id"
            )
            if await self._characters.get(project_id, leader_id) is None:
                raise NotFoundError("领袖人物不存在")
        if payload.capital_city_id is not None:
            capital_id = require_id(payload.capital_city_id, EntityPrefix.CITY, field="capital_city_id")
            if await self._cities.get(project_id, capital_id) is None:
                raise NotFoundError("都城不存在")

    def _to_faction_read(self, faction: Faction) -> FactionRead:
        leader = None
        if faction.leader_character is not None:
            leader = CharacterRef(
                id=faction.leader_character.id,
                code=faction.leader_character.code,
                name=faction.leader_character.name,
            )
        capital = None
        if faction.capital_city is not None:
            capital = CityRef(
                id=faction.capital_city.id,
                code=faction.capital_city.code,
                name=faction.capital_city.name,
            )
        return FactionRead(
            id=faction.id,
            project_id=faction.project_id,
            code=faction.code,
            name=faction.name,
            color=faction.color,
            leader=leader,
            capital=capital,
            start_year=faction.start_year,
            end_year=faction.end_year,
            historical_description=faction.historical_description,
        )

    def _to_member_read(self, member: FactionMember) -> FactionMemberRead:
        return FactionMemberRead(
            id=member.id,
            faction=FactionRef(
                id=member.faction.id,
                code=member.faction.code,
                name=member.faction.name,
                color=member.faction.color,
            ),
            character=CharacterRef(
                id=member.character.id,
                code=member.character.code,
                name=member.character.name,
            ),
            role=FactionMemberRole(member.role),
            start_year=member.start_year,
            end_year=member.end_year,
            note=member.note,
        )

    def _to_territory_read(self, territory: FactionTerritory) -> FactionTerritoryRead:
        return FactionTerritoryRead(
            id=territory.id,
            faction=FactionRef(
                id=territory.faction.id,
                code=territory.faction.code,
                name=territory.faction.name,
                color=territory.faction.color,
            ),
            city=CityRef(id=territory.city.id, code=territory.city.code, name=territory.city.name),
            start_year=territory.start_year,
            end_year=territory.end_year,
            note=territory.note,
        )

    async def _require_faction(self, project_id: str, faction_id: str) -> Faction:
        faction = await self._factions.get(project_id, faction_id)
        if faction is None:
            raise NotFoundError("势力不存在")
        return faction

    async def _require_project(self, project_id: str):
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
