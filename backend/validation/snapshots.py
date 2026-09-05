"""校验用只读快照。与 ORM 解耦，便于单测。"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.story_rules import GraphEdge, GraphNode


@dataclass(frozen=True)
class CharacterSnap:
    """人物生卒。"""

    id: str
    name: str
    birth_year: int | None
    death_year: int | None


@dataclass(frozen=True)
class CitySnap:
    """城池存续。"""

    id: str
    name: str
    founded_year: int | None
    destroyed_year: int | None


@dataclass(frozen=True)
class FactionSnap:
    """势力存续。"""

    id: str
    name: str
    start_year: int | None
    end_year: int | None


@dataclass(frozen=True)
class EventParticipantSnap:
    """事件参与者。"""

    character_id: str
    character_name: str
    birth_year: int | None
    death_year: int | None


@dataclass(frozen=True)
class EventFactionSnap:
    """事件牵涉势力。"""

    faction_id: str
    faction_name: str
    start_year: int | None
    end_year: int | None


@dataclass(frozen=True)
class EventSnap:
    """事件编年。"""

    id: str
    name: str
    year: int
    layer: str
    location_city_id: str | None
    participants: tuple[EventParticipantSnap, ...]
    factions: tuple[EventFactionSnap, ...]
    source_types: tuple[str, ...]


@dataclass(frozen=True)
class TerritorySnap:
    """城池时序归属。"""

    id: str
    city_id: str
    city_name: str
    faction_id: str
    faction_name: str
    start_year: int | None
    end_year: int | None


@dataclass(frozen=True)
class MemberSnap:
    """人物入势时段。"""

    id: str
    character_id: str
    character_name: str
    faction_id: str
    faction_name: str
    start_year: int | None
    end_year: int | None
    birth_year: int | None
    death_year: int | None


@dataclass(frozen=True)
class RelationshipSnap:
    """人物关系时段。"""

    id: str
    from_id: str
    to_id: str
    from_birth: int | None
    from_death: int | None
    to_birth: int | None
    to_death: int | None
    start_year: int | None
    end_year: int | None


@dataclass(frozen=True)
class StorySnap:
    """剧情图。"""

    id: str
    name: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


@dataclass(frozen=True)
class ResourceSnap:
    """资源文件状态。"""

    id: str
    name: str
    path: str
    exists: bool
    checksum_ok: bool


@dataclass
class ProjectSnapshot:
    """项目只读切片。"""

    characters: list[CharacterSnap] = field(default_factory=list)
    cities: list[CitySnap] = field(default_factory=list)
    factions: list[FactionSnap] = field(default_factory=list)
    events: list[EventSnap] = field(default_factory=list)
    territories: list[TerritorySnap] = field(default_factory=list)
    members: list[MemberSnap] = field(default_factory=list)
    relationships: list[RelationshipSnap] = field(default_factory=list)
    stories: list[StorySnap] = field(default_factory=list)
    resources: list[ResourceSnap] = field(default_factory=list)
