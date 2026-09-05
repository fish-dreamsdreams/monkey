"""地图仓储。"""

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.map import GameMap, MapFeature, TerrainCell


class MapRepository:
    """地图、地形与地物持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, game_map: GameMap) -> GameMap:
        """插入地图。"""
        self._session.add(game_map)
        await self._session.flush()
        return game_map

    async def get(self, project_id: str, map_id: str) -> GameMap | None:
        """按 ID 加载地图。"""
        result = await self._session.execute(
            select(GameMap).where(GameMap.project_id == project_id, GameMap.id == map_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> GameMap | None:
        """按业务 code 加载地图。"""
        result = await self._session.execute(
            select(GameMap).where(GameMap.project_id == project_id, GameMap.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[GameMap]:
        """列出项目地图。"""
        result = await self._session.execute(
            select(GameMap).where(GameMap.project_id == project_id).order_by(GameMap.name, GameMap.code)
        )
        return list(result.scalars().all())

    async def delete(self, game_map: GameMap) -> None:
        """删除地图（级联地形与地物）。"""
        await self._session.delete(game_map)
        await self._session.flush()

    async def count_cells(self, map_id: str) -> int:
        """已覆盖地形格数量。"""
        result = await self._session.execute(
            select(func.count()).select_from(TerrainCell).where(TerrainCell.map_id == map_id)
        )
        return int(result.scalar_one())

    async def count_features(self, map_id: str) -> int:
        """地物数量。"""
        result = await self._session.execute(
            select(func.count()).select_from(MapFeature).where(MapFeature.map_id == map_id)
        )
        return int(result.scalar_one())

    async def list_cells(
        self,
        map_id: str,
        x_min: int | None = None,
        y_min: int | None = None,
        x_max: int | None = None,
        y_max: int | None = None,
    ) -> list[TerrainCell]:
        """列出稀疏地形，可按矩形裁切。"""
        stmt = select(TerrainCell).where(TerrainCell.map_id == map_id)
        if x_min is not None:
            stmt = stmt.where(TerrainCell.x >= x_min)
        if y_min is not None:
            stmt = stmt.where(TerrainCell.y >= y_min)
        if x_max is not None:
            stmt = stmt.where(TerrainCell.x <= x_max)
        if y_max is not None:
            stmt = stmt.where(TerrainCell.y <= y_max)
        stmt = stmt.order_by(TerrainCell.y, TerrainCell.x)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_cells_at(self, map_id: str, coords: list[tuple[int, int]]) -> list[TerrainCell]:
        """按坐标批量加载地形格。"""
        if not coords:
            return []
        result = await self._session.execute(
            select(TerrainCell).where(
                TerrainCell.map_id == map_id,
                tuple_(TerrainCell.x, TerrainCell.y).in_(coords),
            )
        )
        return list(result.scalars().all())

    async def add_cell(self, cell: TerrainCell) -> TerrainCell:
        """插入地形格。"""
        self._session.add(cell)
        await self._session.flush()
        return cell

    async def delete_cell(self, cell: TerrainCell) -> None:
        """删除地形覆盖。"""
        await self._session.delete(cell)
        await self._session.flush()

    async def add_feature(self, feature: MapFeature) -> MapFeature:
        """插入地物。"""
        self._session.add(feature)
        await self._session.flush()
        return feature

    async def get_feature(self, map_id: str, feature_id: str) -> MapFeature | None:
        """加载地物。"""
        result = await self._session.execute(
            select(MapFeature).where(MapFeature.map_id == map_id, MapFeature.id == feature_id)
        )
        return result.scalar_one_or_none()

    async def get_feature_by_code(self, map_id: str, code: str) -> MapFeature | None:
        """按 code 加载地物。"""
        result = await self._session.execute(
            select(MapFeature).where(MapFeature.map_id == map_id, MapFeature.code == code)
        )
        return result.scalar_one_or_none()

    async def list_features(self, map_id: str) -> list[MapFeature]:
        """列出地图地物。"""
        result = await self._session.execute(
            select(MapFeature)
            .where(MapFeature.map_id == map_id)
            .order_by(MapFeature.feature_type, MapFeature.name, MapFeature.code)
        )
        return list(result.scalars().all())

    async def delete_feature(self, feature: MapFeature) -> None:
        """删除地物。"""
        await self._session.delete(feature)
        await self._session.flush()
