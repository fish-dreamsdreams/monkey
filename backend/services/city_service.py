"""城池应用服务。

职责：维护城池史实与游戏数值。当前归属不写入城池表。
"""

from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_id
from backend.domain.faction_rules import validate_city_years
from backend.domain.year_range import contains_year
from backend.models.city import City
from backend.repositories.city_repository import CityRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.city import CityGameData, CityHistoricalData, CityRead, CityWrite, FactionRef


class CityService:
    """城池用例编排。"""

    def __init__(
        self,
        cities: CityRepository,
        factions: FactionRepository,
        projects: ProjectRepository,
    ) -> None:
        self._cities = cities
        self._factions = factions
        self._projects = projects

    async def create(self, project_id: str, payload: CityWrite) -> CityRead:
        """创建城池。"""
        await self._require_project(project_id)
        validate_city_years(payload.historical.founded_year, payload.historical.destroyed_year)
        if await self._cities.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"城池 code 已存在: {payload.code}")
        city = self._build(project_id, new_id(EntityPrefix.CITY), payload)
        await self._cities.add(city)
        await self._bump(project_id)
        return self._to_read(city)

    async def get(self, project_id: str, city_id: str, at_year: int | None = None) -> CityRead:
        """获取城池；指定年份时派生 owner。"""
        city = await self._require_city(project_id, city_id)
        return await self._to_read_with_owner(project_id, city, at_year)

    async def list_cities(self, project_id: str, at_year: int | None = None) -> list[CityRead]:
        """列出城池。"""
        await self._require_project(project_id)
        items = await self._cities.list_by_project(project_id)
        return [await self._to_read_with_owner(project_id, item, at_year) for item in items]

    async def update(self, project_id: str, city_id: str, payload: CityWrite) -> CityRead:
        """更新城池。"""
        city = await self._require_city(project_id, city_id)
        validate_city_years(payload.historical.founded_year, payload.historical.destroyed_year)
        duplicate = await self._cities.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != city.id:
            raise ConflictError(f"城池 code 已存在: {payload.code}")
        self._apply(city, payload)
        await self._bump(project_id)
        return self._to_read(city)

    async def delete(self, project_id: str, city_id: str) -> None:
        """删除城池（领土记录级联删除）。"""
        city = await self._require_city(project_id, city_id)
        await self._cities.delete(city)
        await self._bump(project_id)

    def _build(self, project_id: str, city_id: str, payload: CityWrite) -> City:
        city = City(id=city_id, project_id=project_id)
        self._apply(city, payload)
        return city

    def _apply(self, city: City, payload: CityWrite) -> None:
        city.code = payload.code
        city.name = payload.name
        city.coord_x = payload.coord_x
        city.coord_y = payload.coord_y
        city.historical_name = payload.historical.historical_name
        city.founded_year = payload.historical.founded_year
        city.destroyed_year = payload.historical.destroyed_year
        city.historical_description = payload.historical.description
        city.population = payload.game.population
        city.military = payload.game.military
        city.economy = payload.game.economy
        city.defense = payload.game.defense

    def _to_read(self, city: City, owner: FactionRef | None = None) -> CityRead:
        return CityRead(
            id=city.id,
            project_id=city.project_id,
            map_id=city.map_id,
            code=city.code,
            name=city.name,
            coord_x=city.coord_x,
            coord_y=city.coord_y,
            historical=CityHistoricalData(
                historical_name=city.historical_name,
                founded_year=city.founded_year,
                destroyed_year=city.destroyed_year,
                description=city.historical_description,
            ),
            game=CityGameData(
                population=city.population,
                military=city.military,
                economy=city.economy,
                defense=city.defense,
            ),
            owner=owner,
        )

    async def _to_read_with_owner(self, project_id: str, city: City, at_year: int | None) -> CityRead:
        if at_year is None:
            return self._to_read(city)
        territories = await self._factions.list_territories_for_city(project_id, city.id)
        matches = [
            item for item in territories if contains_year(item.start_year, item.end_year, at_year)
        ]
        if len(matches) > 1:
            raise ConflictError(f"城池 {city.name} 在 {at_year} 年存在重叠归属")
        owner = None
        if matches:
            faction = matches[0].faction
            owner = FactionRef(id=faction.id, code=faction.code, name=faction.name, color=faction.color)
        return self._to_read(city, owner)

    async def _require_city(self, project_id: str, city_id: str) -> City:
        city = await self._cities.get(project_id, city_id)
        if city is None:
            raise NotFoundError("城池不存在")
        return city

    async def _require_project(self, project_id: str):
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
