"""历史事件 Schema。后果仅为文本，不触发游戏逻辑。"""

from pydantic import BaseModel, Field, field_validator

from backend.domain.event_rules import EventFactionRole, EventParticipantRole, EventType
from backend.domain.source_types import BoundLayer, SourceType
from backend.schemas.city import CityRef, FactionRef
from backend.schemas.relationship import CharacterRef


class EventWrite(BaseModel):
    """创建或更新事件正文。参与者与引文走独立接口。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    event_type: EventType = EventType.OTHER
    layer: BoundLayer = BoundLayer.HISTORICAL
    year: int = Field(ge=-500, le=3000)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    location_city_id: str | None = Field(default=None, min_length=36, max_length=36)
    location_note: str | None = Field(default=None, max_length=200)
    description: str | None = None
    consequences: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class EventParticipantWrite(BaseModel):
    """人物参与事件。"""

    character_id: str = Field(min_length=36, max_length=36)
    role: EventParticipantRole = EventParticipantRole.PARTICIPANT
    note: str | None = None


class EventParticipantRead(BaseModel):
    """事件参与者。"""

    id: str
    character: CharacterRef
    role: EventParticipantRole
    note: str | None


class EventFactionWrite(BaseModel):
    """势力牵涉事件。"""

    faction_id: str = Field(min_length=36, max_length=36)
    role: EventFactionRole = EventFactionRole.INVOLVED
    note: str | None = None


class EventFactionRead(BaseModel):
    """事件相关势力。"""

    id: str
    faction: FactionRef
    role: EventFactionRole
    note: str | None


class EventSourceWrite(BaseModel):
    """为事件挂一条史源。"""

    source_code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    quotation: str | None = None
    reference: str | None = Field(default=None, max_length=200)
    note: str | None = None

    @field_validator("source_code")
    @classmethod
    def normalize_source_code(cls, value: str) -> str:
        return value.strip().lower()


class EventSourceRead(BaseModel):
    """事件引文。"""

    id: str
    source_id: str
    source_code: str
    source_name: str
    source_type: SourceType
    quotation: str | None
    reference: str | None
    note: str | None
    fact_eligible: bool


class EventRead(BaseModel):
    """事件详情。"""

    id: str
    project_id: str
    code: str
    name: str
    event_type: EventType
    layer: BoundLayer
    year: int
    month: int | None
    day: int | None
    location: CityRef | None
    location_note: str | None
    description: str | None
    consequences: str | None
    participants: list[EventParticipantRead]
    factions: list[EventFactionRead]
    sources: list[EventSourceRead]


class EventSummary(BaseModel):
    """事件列表项。"""

    id: str
    project_id: str
    code: str
    name: str
    event_type: EventType
    layer: BoundLayer
    year: int
    month: int | None
    day: int | None
    location: CityRef | None
    participant_count: int
    faction_count: int
