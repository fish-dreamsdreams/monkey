"""地图应用服务。

职责：维护地图元数据、分块地形与矢量地物，并把城池挂到格子上。不生成预览图。
"""

from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.map_rules import (
    MapFeatureType,
    TerrainType,
    validate_cell_in_bounds,
    validate_city_in_bounds,
    validate_feature_points,
    validate_map_size,
    validate_terrain_patch_size,
)
from backend.models.map import GameMap, MapFeature, TerrainCell
from backend.repositories.city_repository import CityRepository
from backend.repositories.map_repository import MapRepository
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.map import (
    MapCityPlace,
    MapCityRead,
    MapFeatureRead,
    MapFeatureWrite,
    MapPoint,
    MapRead,
    MapSummary,
    MapWrite,
    TerrainCellRead,
    TerrainPatchWrite,
)


class MapService:
    """地图用例编排。"""

    def __init__(
        self,
        maps: MapRepository,
        cities: CityRepository,
        projects: ProjectRepository,
    ) -> None:
        self._maps = maps
        self._cities = cities
        self._projects = projects

    async def create(self, project_id: str, payload: MapWrite) -> MapRead:
        """创建空白地图，不预填全部地块。"""
        await self._require_project(project_id)
        validate_map_size(payload.width, payload.height)
        if await self._maps.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"地图 code 已存在: {payload.code}")
        game_map = GameMap(id=new_id(EntityPrefix.MAP), project_id=project_id)
        self._apply_meta(game_map, payload)
        await self._maps.add(game_map)
        await self._bump(project_id)
        return await self._to_read(game_map)

    async def get(self, project_id: str, map_id: str) -> MapRead:
        """获取地图（地物与城池，不含完整网格）。"""
        return await self._to_read(await self._require_map(project_id, map_id))

    async def list_maps(self, project_id: str) -> list[MapSummary]:
        """列出项目地图。"""
        await self._require_project(project_id)
        items = await self._maps.list_by_project(project_id)
        summaries: list[MapSummary] = []
        for item in items:
            summaries.append(
                MapSummary(
                    id=item.id,
                    project_id=item.project_id,
                    code=item.code,
                    name=item.name,
                    width=item.width,
                    height=item.height,
                    cell_size=item.cell_size,
                    default_terrain=TerrainType(item.default_terrain),
                    terrain_cell_count=await self._maps.count_cells(item.id),
                    city_count=len(await self._cities.list_by_map(item.id)),
                    feature_count=await self._maps.count_features(item.id),
                )
            )
        return summaries

    async def update(self, project_id: str, map_id: str, payload: MapWrite) -> MapRead:
        """更新地图尺寸与默认地形。缩小后越界数据拒绝保存。"""
        game_map = await self._require_map(project_id, map_id)
        validate_map_size(payload.width, payload.height)
        duplicate = await self._maps.get_by_code(project_id, payload.code)
        if duplicate is not None and duplicate.id != game_map.id:
            raise ConflictError(f"地图 code 已存在: {payload.code}")
        await self._assert_resize_safe(game_map, payload.width, payload.height)
        self._apply_meta(game_map, payload)
        await self._bump(project_id)
        return await self._to_read(game_map)

    async def delete(self, project_id: str, map_id: str) -> None:
        """删除地图。城池 map_id 置空。"""
        game_map = await self._require_map(project_id, map_id)
        await self._maps.delete(game_map)
        await self._bump(project_id)

    async def list_terrain(
        self,
        project_id: str,
        map_id: str,
        x_min: int | None = None,
        y_min: int | None = None,
        x_max: int | None = None,
        y_max: int | None = None,
    ) -> list[TerrainCellRead]:
        """读取稀疏地形。"""
        await self._require_map(project_id, map_id)
        cells = await self._maps.list_cells(map_id, x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)
        return [TerrainCellRead(x=item.x, y=item.y, terrain=TerrainType(item.terrain)) for item in cells]

    async def patch_terrain(
        self, project_id: str, map_id: str, payload: TerrainPatchWrite
    ) -> list[TerrainCellRead]:
        """分块覆盖或删除地形格。"""
        game_map = await self._require_map(project_id, map_id)
        validate_terrain_patch_size(len(payload.cells))
        coords = [(item.x, item.y) for item in payload.cells]
        if len(set(coords)) != len(coords):
            raise ValidationError("同一补丁内不能重复同一格子", field="cells")
        existing = {(item.x, item.y): item for item in await self._maps.list_cells_at(map_id, coords)}
        for item in payload.cells:
            validate_cell_in_bounds(item.x, item.y, game_map.width, game_map.height)
            current = existing.get((item.x, item.y))
            if item.terrain is None:
                if current is not None:
                    await self._maps.delete_cell(current)
                continue
            if current is None:
                await self._maps.add_cell(
                    TerrainCell(
                        id=new_id(EntityPrefix.TERRAIN_CELL),
                        map_id=map_id,
                        x=item.x,
                        y=item.y,
                        terrain=item.terrain.value,
                    )
                )
            else:
                current.terrain = item.terrain.value
        await self._bump(project_id)
        return await self.list_terrain(project_id, map_id)

    async def add_feature(self, project_id: str, map_id: str, payload: MapFeatureWrite) -> MapFeatureRead:
        """新增矢量地物。"""
        game_map = await self._require_map(project_id, map_id)
        self._validate_feature(game_map, payload)
        if await self._maps.get_feature_by_code(map_id, payload.code) is not None:
            raise ConflictError(f"地物 code 已存在: {payload.code}")
        feature = MapFeature(
            id=new_id(EntityPrefix.MAP_FEATURE),
            map_id=map_id,
            code=payload.code,
            name=payload.name,
            feature_type=payload.feature_type.value,
            geometry=[point.model_dump() for point in payload.points],
            note=payload.note,
        )
        await self._maps.add_feature(feature)
        await self._bump(project_id)
        return self._to_feature_read(feature)

    async def update_feature(
        self, project_id: str, map_id: str, feature_id: str, payload: MapFeatureWrite
    ) -> MapFeatureRead:
        """更新地物。"""
        game_map = await self._require_map(project_id, map_id)
        feature = await self._maps.get_feature(map_id, feature_id)
        if feature is None:
            raise NotFoundError("地物不存在")
        self._validate_feature(game_map, payload)
        duplicate = await self._maps.get_feature_by_code(map_id, payload.code)
        if duplicate is not None and duplicate.id != feature.id:
            raise ConflictError(f"地物 code 已存在: {payload.code}")
        feature.code = payload.code
        feature.name = payload.name
        feature.feature_type = payload.feature_type.value
        feature.geometry = [point.model_dump() for point in payload.points]
        feature.note = payload.note
        await self._bump(project_id)
        return self._to_feature_read(feature)

    async def delete_feature(self, project_id: str, map_id: str, feature_id: str) -> None:
        """删除地物。"""
        await self._require_map(project_id, map_id)
        feature = await self._maps.get_feature(map_id, feature_id)
        if feature is None:
            raise NotFoundError("地物不存在")
        await self._maps.delete_feature(feature)
        await self._bump(project_id)

    async def place_city(self, project_id: str, map_id: str, payload: MapCityPlace) -> MapCityRead:
        """把城池挂到地图格子。同一格不能放两座城。"""
        game_map = await self._require_map(project_id, map_id)
        city_id = require_id(payload.city_id, EntityPrefix.CITY, field="city_id")
        city = await self._cities.get(project_id, city_id)
        if city is None:
            raise NotFoundError("城池不存在")
        validate_city_in_bounds(payload.coord_x, payload.coord_y, game_map.width, game_map.height)
        occupant = await self._cities.get_at_cell(map_id, payload.coord_x, payload.coord_y)
        if occupant is not None and occupant.id != city.id:
            raise ConflictError("该格子已有其他城池")
        city.map_id = map_id
        city.coord_x = payload.coord_x
        city.coord_y = payload.coord_y
        await self._bump(project_id)
        return MapCityRead(id=city.id, code=city.code, name=city.name, coord_x=city.coord_x, coord_y=city.coord_y)

    async def unplace_city(self, project_id: str, map_id: str, city_id: str) -> None:
        """从地图卸下城池，保留城池记录。"""
        await self._require_map(project_id, map_id)
        city = await self._cities.get(project_id, city_id)
        if city is None or city.map_id != map_id:
            raise NotFoundError("城池未挂在该地图上")
        city.map_id = None
        await self._bump(project_id)

    def _apply_meta(self, game_map: GameMap, payload: MapWrite) -> None:
        game_map.code = payload.code
        game_map.name = payload.name
        game_map.width = payload.width
        game_map.height = payload.height
        game_map.cell_size = payload.cell_size
        game_map.default_terrain = payload.default_terrain.value
        game_map.description = payload.description

    def _validate_feature(self, game_map: GameMap, payload: MapFeatureWrite) -> None:
        validate_feature_points(
            payload.feature_type,
            [(point.x, point.y) for point in payload.points],
            game_map.width,
            game_map.height,
        )

    async def _assert_resize_safe(self, game_map: GameMap, width: int, height: int) -> None:
        cells = await self._maps.list_cells(game_map.id)
        if any(item.x >= width or item.y >= height for item in cells):
            raise ValidationError("缩小地图前请先清除越界地形", field="width")
        features = await self._maps.list_features(game_map.id)
        for feature in features:
            points = [(float(point["x"]), float(point["y"])) for point in feature.geometry]
            try:
                validate_feature_points(MapFeatureType(feature.feature_type), points, width, height)
            except ValidationError as exc:
                raise ValidationError("缩小地图前请先调整越界地物", field="width") from exc
        for city in await self._cities.list_by_map(game_map.id):
            if city.coord_x is None or city.coord_y is None:
                continue
            if city.coord_x >= width or city.coord_y >= height:
                raise ValidationError("缩小地图前请先移动越界城池", field="width")

    async def _to_read(self, game_map: GameMap) -> MapRead:
        features = [self._to_feature_read(item) for item in await self._maps.list_features(game_map.id)]
        cities = [
            MapCityRead(
                id=item.id,
                code=item.code,
                name=item.name,
                coord_x=item.coord_x or 0,
                coord_y=item.coord_y or 0,
            )
            for item in await self._cities.list_by_map(game_map.id)
        ]
        return MapRead(
            id=game_map.id,
            project_id=game_map.project_id,
            code=game_map.code,
            name=game_map.name,
            width=game_map.width,
            height=game_map.height,
            cell_size=game_map.cell_size,
            default_terrain=TerrainType(game_map.default_terrain),
            description=game_map.description,
            terrain_cell_count=await self._maps.count_cells(game_map.id),
            cities=cities,
            features=features,
        )

    def _to_feature_read(self, feature: MapFeature) -> MapFeatureRead:
        return MapFeatureRead(
            id=feature.id,
            code=feature.code,
            name=feature.name,
            feature_type=MapFeatureType(feature.feature_type),
            points=[MapPoint(x=float(point["x"]), y=float(point["y"])) for point in feature.geometry],
            note=feature.note,
        )

    async def _require_map(self, project_id: str, map_id: str) -> GameMap:
        game_map = await self._maps.get(project_id, map_id)
        if game_map is None:
            raise NotFoundError("地图不存在")
        return game_map

    async def _require_project(self, project_id: str):
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
