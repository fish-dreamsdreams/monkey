"""剧情 Schema。节点图属于游戏叙事层，不结算战斗。"""

from pydantic import BaseModel, Field, field_validator

from backend.domain.source_types import BoundLayer
from backend.domain.story_rules import (
    StoryActionType,
    StoryCastRole,
    StoryConditionType,
    StoryNodeType,
)
from backend.schemas.city import CityRef, FactionRef
from backend.schemas.relationship import CharacterRef


class EventRef(BaseModel):
    """剧情节点引用的历史事件摘要。"""

    id: str
    code: str
    name: str
    year: int


class StoryWrite(BaseModel):
    """创建或更新剧情正文。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    layer: BoundLayer = BoundLayer.LITERARY
    description: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("layer")
    @classmethod
    def reject_historical_layer(cls, value: BoundLayer) -> BoundLayer:
        if value == BoundLayer.HISTORICAL:
            raise ValueError("剧情属于叙事层，不能标记为 historical")
        return value


class StoryChapterWrite(BaseModel):
    """章节。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    sort_order: int = Field(default=0, ge=0, le=10000)
    summary: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class StoryChapterRead(BaseModel):
    """章节详情。"""

    id: str
    code: str
    name: str
    sort_order: int
    summary: str | None


class StoryNodeWrite(BaseModel):
    """创建或更新节点。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    node_type: StoryNodeType
    chapter_id: str | None = Field(default=None, min_length=36, max_length=36)
    is_entry: bool = False
    is_ending: bool = False
    sort_order: int = Field(default=0, ge=0, le=10000)
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None
    event_id: str | None = Field(default=None, min_length=36, max_length=36)
    character_id: str | None = Field(default=None, min_length=36, max_length=36)
    city_id: str | None = Field(default=None, min_length=36, max_length=36)
    faction_id: str | None = Field(default=None, min_length=36, max_length=36)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class StoryEdgeWrite(BaseModel):
    """从当前节点连到目标节点。"""

    to_node_id: str = Field(min_length=36, max_length=36)
    is_conditional: bool = False
    condition_note: str | None = None
    sort_order: int = Field(default=0, ge=0, le=10000)


class StoryChoiceWrite(BaseModel):
    """选项，同时创建一条边。"""

    label: str = Field(min_length=1, max_length=200)
    to_node_id: str = Field(min_length=36, max_length=36)
    is_conditional: bool = False
    condition_note: str | None = None
    sort_order: int = Field(default=0, ge=0, le=10000)


class StoryConditionWrite(BaseModel):
    """节点条件。"""

    condition_type: StoryConditionType
    expression: str | None = None
    note: str | None = None


class StoryActionWrite(BaseModel):
    """节点动作。"""

    action_type: StoryActionType
    expression: str | None = None
    note: str | None = None


class StoryCastWrite(BaseModel):
    """节点出场人物。"""

    character_id: str = Field(min_length=36, max_length=36)
    role: StoryCastRole = StoryCastRole.PRESENT
    note: str | None = None


class StoryConditionRead(BaseModel):
    """条件读取。"""

    id: str
    condition_type: StoryConditionType
    expression: str | None
    note: str | None


class StoryActionRead(BaseModel):
    """动作读取。"""

    id: str
    action_type: StoryActionType
    expression: str | None
    note: str | None


class StoryCastRead(BaseModel):
    """出场人物读取。"""

    id: str
    character: CharacterRef
    role: StoryCastRole
    note: str | None


class StoryChoiceRead(BaseModel):
    """选项读取。"""

    id: str
    label: str
    to_node_id: str | None
    sort_order: int


class StoryEdgeRead(BaseModel):
    """边读取。"""

    id: str
    from_node_id: str
    to_node_id: str
    choice_id: str | None
    is_conditional: bool
    condition_note: str | None
    sort_order: int


class StoryNodeRead(BaseModel):
    """节点详情。"""

    id: str
    chapter_id: str | None
    code: str
    name: str
    node_type: StoryNodeType
    is_entry: bool
    is_ending: bool
    sort_order: int
    title: str | None
    body: str | None
    event: EventRef | None
    character: CharacterRef | None
    city: CityRef | None
    faction: FactionRef | None
    outgoing: list[StoryEdgeRead]
    choices: list[StoryChoiceRead]
    conditions: list[StoryConditionRead]
    actions: list[StoryActionRead]
    cast: list[StoryCastRead]


class StoryGraphRead(BaseModel):
    """节点图校验结果。"""

    valid: bool
    errors: list[str]
    has_unconditional_cycle: bool
    entry_reaches_ending: bool
    entry_count: int
    ending_count: int
    node_count: int
    edge_count: int


class StoryRead(BaseModel):
    """剧情详情。"""

    id: str
    project_id: str
    code: str
    name: str
    layer: BoundLayer
    description: str | None
    chapters: list[StoryChapterRead]
    nodes: list[StoryNodeRead]
    graph: StoryGraphRead


class StorySummary(BaseModel):
    """剧情列表项。"""

    id: str
    project_id: str
    code: str
    name: str
    layer: BoundLayer
    node_count: int
    chapter_count: int
    graph_valid: bool
