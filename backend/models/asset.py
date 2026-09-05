"""资源与模型扩展表。

职责：只存资源元数据与相对路径。人物等实体通过外键引用，不把路径散写在各表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.project import Project


class Resource(Base):
    """项目内资源登记。path 相对项目 assets 根，不存绝对路径。"""

    __tablename__ = "resources"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_resource_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    path: Mapped[str] = mapped_column(String(200), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preview_path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="resources")
    model_asset: Mapped[ModelAsset | None] = relationship(
        back_populates="resource",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ModelAsset(Base):
    """模型类资源的扩展信息。不加载网格，不播放动画。"""

    __tablename__ = "model_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resource_id: Mapped[str] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    mesh_format: Mapped[str] = mapped_column(String(16), nullable=False, default="gltf")
    lod_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    animation_set_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    skeleton_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="model_asset")
