"""剧情、章节、节点与边。

职责：保存游戏叙事层的节点图。不执行对白、选项或战斗。可引用历史事件，但不改写史实栏。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.character import Character
    from backend.models.city import City
    from backend.models.event import HistoricalEvent
    from backend.models.faction import Faction
    from backend.models.project import Project


class Story(Base):
    """一条剧情。属于游戏叙事层，不是正史编年。"""

    __tablename__ = "stories"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_story_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    layer: Mapped[str] = mapped_column(String(16), nullable=False, default="literary")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="stories")
    chapters: Mapped[list[StoryChapter]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
    )
    nodes: Mapped[list[StoryNode]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
    )


class StoryChapter(Base):
    """剧情章节，仅作节点分组。"""

    __tablename__ = "story_chapters"
    __table_args__ = (UniqueConstraint("story_id", "code", name="uq_chapter_story_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    story: Mapped[Story] = relationship(back_populates="chapters")
    nodes: Mapped[list[StoryNode]] = relationship(back_populates="chapter")


class StoryNode(Base):
    """剧情节点。is_ending 标记结束，不另设 ending 类型。"""

    __tablename__ = "story_nodes"
    __table_args__ = (UniqueConstraint("story_id", "code", name="uq_node_story_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    chapter_id: Mapped[str | None] = mapped_column(
        ForeignKey("story_chapters.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_ending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_id: Mapped[str | None] = mapped_column(
        ForeignKey("historical_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    character_id: Mapped[str | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )
    city_id: Mapped[str | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )
    faction_id: Mapped[str | None] = mapped_column(
        ForeignKey("factions.id", ondelete="SET NULL"),
        nullable=True,
    )

    story: Mapped[Story] = relationship(back_populates="nodes")
    chapter: Mapped[StoryChapter | None] = relationship(back_populates="nodes")
    event: Mapped[HistoricalEvent | None] = relationship()
    character: Mapped[Character | None] = relationship()
    city: Mapped[City | None] = relationship()
    faction: Mapped[Faction | None] = relationship()
    outgoing: Mapped[list[StoryEdge]] = relationship(
        back_populates="from_node",
        foreign_keys="StoryEdge.from_node_id",
        cascade="all, delete-orphan",
    )
    choices: Mapped[list[StoryChoice]] = relationship(
        back_populates="node",
        cascade="all, delete-orphan",
    )
    conditions: Mapped[list[StoryCondition]] = relationship(
        back_populates="node",
        cascade="all, delete-orphan",
    )
    actions: Mapped[list[StoryAction]] = relationship(
        back_populates="node",
        cascade="all, delete-orphan",
    )
    cast: Mapped[list[StoryNodeCharacter]] = relationship(
        back_populates="node",
        cascade="all, delete-orphan",
    )


class StoryEdge(Base):
    """节点邻接表。条件边可回跳，无条件边禁止成环。"""

    __tablename__ = "story_edges"
    __table_args__ = (UniqueConstraint("from_node_id", "to_node_id", name="uq_story_edge_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    from_node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    to_node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    choice_id: Mapped[str | None] = mapped_column(
        ForeignKey("story_choices.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_conditional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    condition_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    from_node: Mapped[StoryNode] = relationship(
        back_populates="outgoing",
        foreign_keys=[from_node_id],
    )
    to_node: Mapped[StoryNode] = relationship(foreign_keys=[to_node_id])
    choice: Mapped[StoryChoice | None] = relationship(foreign_keys=[choice_id])


class StoryChoice(Base):
    """选项节点上的分支文案。目标由边表达。"""

    __tablename__ = "story_choices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    node: Mapped[StoryNode] = relationship(back_populates="choices")


class StoryCondition(Base):
    """节点条件数据。编辑器不求值。"""

    __tablename__ = "story_conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(32), nullable=False)
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    node: Mapped[StoryNode] = relationship(back_populates="conditions")


class StoryAction(Base):
    """节点动作数据。编辑器不执行。"""

    __tablename__ = "story_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    node: Mapped[StoryNode] = relationship(back_populates="actions")


class StoryNodeCharacter(Base):
    """节点出场人物。"""

    __tablename__ = "story_node_characters"
    __table_args__ = (UniqueConstraint("node_id", "character_id", name="uq_story_node_character"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("story_nodes.id", ondelete="CASCADE"), nullable=False)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="present")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    node: Mapped[StoryNode] = relationship(back_populates="cast")
    character: Mapped[Character] = relationship()
