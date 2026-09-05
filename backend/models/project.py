"""项目表映射。

职责：保存内容项目元数据与版本号，不存储游戏运行状态。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.personality import PersonalityTag
    from backend.models.relationship import CharacterRelationship
    from backend.models.city import City
    from backend.models.event import HistoricalEvent
    from backend.models.faction import Faction
    from backend.models.map import GameMap
    from backend.models.skill import Skill
    from backend.models.source import Source
    from backend.models.asset import Resource
    from backend.models.story import Story


class Project(Base):
    """内容项目。"""

    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("code", name="uq_projects_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.9.0")
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    characters: Mapped[list[Character]] = relationship(back_populates="project")
    personality_tags: Mapped[list[PersonalityTag]] = relationship(back_populates="project")
    sources: Mapped[list[Source]] = relationship(back_populates="project")
    relationships: Mapped[list[CharacterRelationship]] = relationship(back_populates="project")
    skills: Mapped[list[Skill]] = relationship(back_populates="project")
    cities: Mapped[list[City]] = relationship(back_populates="project")
    factions: Mapped[list[Faction]] = relationship(back_populates="project")
    maps: Mapped[list[GameMap]] = relationship(back_populates="project")
    events: Mapped[list[HistoricalEvent]] = relationship(back_populates="project")
    stories: Mapped[list[Story]] = relationship(back_populates="project")
    resources: Mapped[list[Resource]] = relationship(back_populates="project")
