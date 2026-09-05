"""性格标签表映射。

职责：以结构化标签存储人物性格，禁止把性格写成一段自由文本。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.project import Project


class PersonalityTag(Base):
    """项目内性格标签。系统预置标签可扩展。"""

    __tablename__ = "personality_tags"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_personality_tag_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    project: Mapped[Project] = relationship(back_populates="personality_tags")
    bindings: Mapped[list[CharacterPersonality]] = relationship(back_populates="tag")


class CharacterPersonality(Base):
    """人物与性格标签的多对多绑定。"""

    __tablename__ = "character_personalities"

    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    personality_tag_id: Mapped[str] = mapped_column(
        ForeignKey("personality_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    character: Mapped[Character] = relationship(back_populates="personalities")
    tag: Mapped[PersonalityTag] = relationship(back_populates="bindings")
