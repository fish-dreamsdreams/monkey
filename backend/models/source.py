"""史料目录与人物引文。

职责：保存可复用的来源条目，以及人物对来源的引文；不把演义内容写入史实表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.project import Project


class Source(Base):
    """项目内史料/文献目录。"""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_source_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    project: Mapped[Project] = relationship(back_populates="sources")
    citations: Mapped[list[CharacterSource]] = relationship(back_populates="source")


class CharacterSource(Base):
    """人物引文。bound_layer 决定它支撑史实栏、演义层还是游戏设定。"""

    __tablename__ = "character_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    bound_layer: Mapped[str] = mapped_column(String(16), nullable=False)
    quotation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped[Character] = relationship(back_populates="citations")
    source: Mapped[Source] = relationship(back_populates="citations")
