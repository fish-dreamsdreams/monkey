"""历史事件、参与者、势力与史源。

职责：记录编年事件。后果只是文本，不驱动游戏引擎。参与关系用关联表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.city import City
    from backend.models.faction import Faction
    from backend.models.project import Project
    from backend.models.source import Source


class HistoricalEvent(Base):
    """历史或演义事件。layer 决定它能否引用正史以外的来源。"""

    __tablename__ = "historical_events"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_event_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    layer: Mapped[str] = mapped_column(String(16), nullable=False, default="historical")
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_city_id: Mapped[str | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )
    location_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    consequences: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="events")
    location_city: Mapped[City | None] = relationship()
    participants: Mapped[list[EventParticipant]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    factions: Mapped[list[EventFaction]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    sources: Mapped[list[EventSource]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventParticipant(Base):
    """人物参与某事件。"""

    __tablename__ = "event_participants"
    __table_args__ = (UniqueConstraint("event_id", "character_id", name="uq_event_character"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("historical_events.id", ondelete="CASCADE"), nullable=False)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="participant")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped[HistoricalEvent] = relationship(back_populates="participants")
    character: Mapped[Character] = relationship()


class EventFaction(Base):
    """势力牵涉某事件。"""

    __tablename__ = "event_factions"
    __table_args__ = (UniqueConstraint("event_id", "faction_id", name="uq_event_faction"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("historical_events.id", ondelete="CASCADE"), nullable=False)
    faction_id: Mapped[str] = mapped_column(ForeignKey("factions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="involved")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped[HistoricalEvent] = relationship(back_populates="factions")
    faction: Mapped[Faction] = relationship()


class EventSource(Base):
    """事件引文。是否能支撑史实层由事件 layer 与来源类型共同决定。"""

    __tablename__ = "event_sources"
    __table_args__ = (UniqueConstraint("event_id", "source_id", name="uq_event_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("historical_events.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    quotation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped[HistoricalEvent] = relationship(back_populates="sources")
    source: Mapped[Source] = relationship()
