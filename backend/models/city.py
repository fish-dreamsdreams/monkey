"""城池表映射。

职责：保存城池身份、史实与游戏数值。当前归属不落在本表，由势力领土按时序派生。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.map import GameMap
    from backend.models.project import Project


class City(Base):
    """城池。owner 不入库，查询某年视图时再派生。"""

    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_city_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    map_id: Mapped[str | None] = mapped_column(ForeignKey("maps.id", ondelete="SET NULL"), nullable=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    historical_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coord_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coord_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destroyed_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    historical_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    military: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    economy: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    defense: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    project: Mapped[Project] = relationship(back_populates="cities")
    game_map: Mapped[GameMap | None] = relationship(back_populates="cities")
