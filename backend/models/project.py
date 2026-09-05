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


class Project(Base):
    """内容项目。"""

    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("code", name="uq_projects_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.1.0")
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
