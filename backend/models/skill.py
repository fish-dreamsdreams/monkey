"""技能定义与人物绑定。

职责：把技能效果存成 JSON 数据供客户端解释；不存储战斗运行时状态，也不执行伤害公式。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.project import Project


class Skill(Base):
    """项目内技能定义。effects / cost / trigger 均为数据，不是可执行代码。"""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_skill_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    skill_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target: Mapped[str] = mapped_column(String(32), nullable=False, default="self")
    cooldown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    trigger_condition: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    effects: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    basis_source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    basis_source_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    basis_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="skills")
    bindings: Mapped[list[CharacterSkill]] = relationship(back_populates="skill", cascade="all, delete-orphan")


class CharacterSkill(Base):
    """人物掌握的技能。来源说明解释为何此人有此技能，不写入史实栏。"""

    __tablename__ = "character_skills"
    __table_args__ = (UniqueConstraint("character_id", "skill_id", name="uq_character_skill"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped[Character] = relationship()
    skill: Mapped[Skill] = relationship(back_populates="bindings")
