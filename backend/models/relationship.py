"""人物关系表映射。

职责：保存有向关系边。对称类型会成对写入，不存储战斗亲密度运行时状态。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.project import Project


class CharacterRelationship(Base):
    """人物关系边。is_primary 标记用户创建的方向，对称关系另有反向边。"""

    __tablename__ = "character_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    pair_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    from_character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    intimacy: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    hostility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project: Mapped[Project] = relationship(back_populates="relationships")
    from_character: Mapped[Character] = relationship(foreign_keys=[from_character_id])
    to_character: Mapped[Character] = relationship(foreign_keys=[to_character_id])
