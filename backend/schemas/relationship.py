"""人物关系 Schema。"""

from pydantic import BaseModel, Field

from backend.domain.relationship_types import RelationshipType


class CharacterRef(BaseModel):
    """关系端点人物摘要。"""

    id: str
    code: str
    name: str


class RelationshipCreate(BaseModel):
    """创建人物关系。对称类型会自动写反向边。"""

    from_character_id: str = Field(min_length=36, max_length=36)
    to_character_id: str = Field(min_length=36, max_length=36)
    relationship_type: RelationshipType
    intimacy: int = Field(default=50, ge=0, le=100)
    hostility: int = Field(default=0, ge=0, le=100)
    start_year: int | None = Field(default=None, ge=-500, le=3000)
    end_year: int | None = Field(default=None, ge=-500, le=3000)
    note: str | None = None


class RelationshipUpdate(BaseModel):
    """更新关系属性。不改两端人物。"""

    relationship_type: RelationshipType
    intimacy: int = Field(default=50, ge=0, le=100)
    hostility: int = Field(default=0, ge=0, le=100)
    start_year: int | None = Field(default=None, ge=-500, le=3000)
    end_year: int | None = Field(default=None, ge=-500, le=3000)
    note: str | None = None


class RelationshipRead(BaseModel):
    """关系详情。"""

    id: str
    project_id: str
    pair_id: str
    from_character: CharacterRef
    to_character: CharacterRef
    relationship_type: RelationshipType
    symmetric: bool
    intimacy: int
    hostility: int
    start_year: int | None
    end_year: int | None
    note: str | None
    is_primary: bool
    direction: str | None = None


class CharacterRelationshipGraph(BaseModel):
    """某个人物的关系邻接表。"""

    character_id: str
    edges: list[RelationshipRead]


class RelationshipTypeMeta(BaseModel):
    """关系类型说明。"""

    code: str
    name_zh: str
    symmetric: bool
