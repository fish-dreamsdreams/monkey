"""SQLAlchemy 映射模型。"""

from backend.models.base import Base
from backend.models.character import Character, CharacterAttribute, CharacterHistoricalRecord
from backend.models.city import City
from backend.models.event import EventFaction, EventParticipant, EventSource, HistoricalEvent
from backend.models.faction import Faction, FactionMember, FactionTerritory
from backend.models.map import GameMap, MapFeature, TerrainCell
from backend.models.personality import CharacterPersonality, PersonalityTag
from backend.models.project import Project
from backend.models.relationship import CharacterRelationship
from backend.models.skill import CharacterSkill, Skill
from backend.models.source import CharacterSource, Source
from backend.models.story import (
    Story,
    StoryAction,
    StoryChapter,
    StoryChoice,
    StoryCondition,
    StoryEdge,
    StoryNode,
    StoryNodeCharacter,
)

__all__ = [
    "Base",
    "Project",
    "Character",
    "CharacterAttribute",
    "CharacterHistoricalRecord",
    "PersonalityTag",
    "CharacterPersonality",
    "Source",
    "CharacterSource",
    "CharacterRelationship",
    "Skill",
    "CharacterSkill",
    "City",
    "Faction",
    "FactionMember",
    "FactionTerritory",
    "GameMap",
    "TerrainCell",
    "MapFeature",
    "HistoricalEvent",
    "EventParticipant",
    "EventFaction",
    "EventSource",
    "Story",
    "StoryChapter",
    "StoryNode",
    "StoryEdge",
    "StoryChoice",
    "StoryCondition",
    "StoryAction",
    "StoryNodeCharacter",
]
