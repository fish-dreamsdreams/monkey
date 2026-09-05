"""人物相关表映射。

职责：把人物拆成身份主表、历史事实表、游戏属性表，避免史实被数值平衡覆盖。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.asset import Resource
    from backend.models.personality import CharacterPersonality
    from backend.models.project import Project
    from backend.models.source import CharacterSource


class Character(Base):
    """人物稳定身份。不存储战斗运行时状态。"""

    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_character_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    courtesy_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    death_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    birthplace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    portrait_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    project: Mapped[Project] = relationship(back_populates="characters")
    historical_record: Mapped[CharacterHistoricalRecord | None] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
        uselist=False,
    )
    attributes: Mapped[list[CharacterAttribute]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    personalities: Mapped[list[CharacterPersonality]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    citations: Mapped[list[CharacterSource]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    portrait_asset: Mapped[Resource | None] = relationship(
        foreign_keys=[portrait_asset_id],
    )
    model_asset: Mapped[Resource | None] = relationship(
        foreign_keys=[model_asset_id],
    )


class CharacterHistoricalRecord(Base):
    """人物历史事实。禁止写入游戏数值。"""

    __tablename__ = "character_historical_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_background: Mapped[str | None] = mapped_column(Text, nullable=True)
    life_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    historical_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped[Character] = relationship(back_populates="historical_record")


class CharacterAttribute(Base):
    """人物游戏属性。可按 version_name 保存多套数值。"""

    __tablename__ = "character_attributes"
    __table_args__ = (
        UniqueConstraint("character_id", "version_name", name="uq_character_attribute_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    version_name: Mapped[str] = mapped_column(String(50), nullable=False, default="default")
    force: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    politics: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    leadership: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    stamina: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    morale: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    mobility: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    character: Mapped[Character] = relationship(back_populates="attributes")
