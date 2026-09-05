"""地图、地形格与矢量地物。

职责：保存 2D 地图数据。地形用稀疏格子；区域/道路/河流/山脉用点列几何。城池通过 map_id 挂接。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.city import City
    from backend.models.project import Project


class GameMap(Base):
    """一张内容地图。不存储渲染图或运行时迷雾。"""

    __tablename__ = "maps"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_map_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_size: Mapped[int] = mapped_column(Integer, nullable=False, default=32)
    default_terrain: Mapped[str] = mapped_column(String(16), nullable=False, default="plain")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="maps")
    cells: Mapped[list[TerrainCell]] = relationship(back_populates="game_map", cascade="all, delete-orphan")
    features: Mapped[list[MapFeature]] = relationship(back_populates="game_map", cascade="all, delete-orphan")
    cities: Mapped[list[City]] = relationship(back_populates="game_map", passive_deletes=True)


class TerrainCell(Base):
    """稀疏地形格。未出现的格子视为 default_terrain。"""

    __tablename__ = "map_terrain_cells"
    __table_args__ = (UniqueConstraint("map_id", "x", "y", name="uq_terrain_map_xy"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    map_id: Mapped[str] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    terrain: Mapped[str] = mapped_column(String(16), nullable=False)

    game_map: Mapped[GameMap] = relationship(back_populates="cells")


class MapFeature(Base):
    """矢量地物：区域、道路、河流、山脉。"""

    __tablename__ = "map_features"
    __table_args__ = (UniqueConstraint("map_id", "code", name="uq_feature_map_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    map_id: Mapped[str] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[str] = mapped_column(String(16), nullable=False)
    geometry: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    game_map: Mapped[GameMap] = relationship(back_populates="features")
