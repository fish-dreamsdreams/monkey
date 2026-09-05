"""势力及其时序成员、领土。

职责：势力由用户创建；人物入势与城池归属都带起止年，禁止写成静态魏蜀吴常量。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.city import City
    from backend.models.project import Project


class Faction(Base):
    """用户创建的势力。领袖与都城只是指针，时序以成员表和领土表为准。"""

    __tablename__ = "factions"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_faction_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#808080")
    leader_character_id: Mapped[str | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )
    capital_city_id: Mapped[str | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    historical_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="factions")
    leader_character: Mapped[Character | None] = relationship(foreign_keys=[leader_character_id])
    capital_city: Mapped[City | None] = relationship(foreign_keys=[capital_city_id])
    members: Mapped[list[FactionMember]] = relationship(
        back_populates="faction",
        cascade="all, delete-orphan",
    )
    territories: Mapped[list[FactionTerritory]] = relationship(
        back_populates="faction",
        cascade="all, delete-orphan",
    )


class FactionMember(Base):
    """人物在某时段加入某势力。"""

    __tablename__ = "faction_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    faction_id: Mapped[str] = mapped_column(ForeignKey("factions.id", ondelete="CASCADE"), nullable=False)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="member")
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    faction: Mapped[Faction] = relationship(back_populates="members")
    character: Mapped[Character] = relationship()


class FactionTerritory(Base):
    """城池在某时段属于某势力。同一时段不能两属。"""

    __tablename__ = "faction_territories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    faction_id: Mapped[str] = mapped_column(ForeignKey("factions.id", ondelete="CASCADE"), nullable=False)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    faction: Mapped[Faction] = relationship(back_populates="territories")
    city: Mapped[City] = relationship()
