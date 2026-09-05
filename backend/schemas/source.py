"""史料目录与人物引文 Schema。"""

from pydantic import BaseModel, Field, field_validator

from backend.domain.source_types import BoundLayer, SourceType


class SourceCreate(BaseModel):
    """新增项目来源。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    source_type: SourceType

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class SourceUpdate(BaseModel):
    """更新自定义来源。code 不可改。"""

    name: str = Field(min_length=1, max_length=100)
    source_type: SourceType


class SourceRead(BaseModel):
    """来源目录条目。"""

    id: str
    project_id: str
    code: str
    name: str
    source_type: SourceType
    is_system: bool
    fact_eligible: bool

    model_config = {"from_attributes": True}


class CharacterSourceWrite(BaseModel):
    """为人物挂一条引文。"""

    source_code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    bound_layer: BoundLayer
    quotation: str | None = None
    reference: str | None = Field(default=None, max_length=200)
    note: str | None = None

    @field_validator("source_code")
    @classmethod
    def normalize_source_code(cls, value: str) -> str:
        return value.strip().lower()


class CharacterSourceRead(BaseModel):
    """人物引文。"""

    id: str
    source_id: str
    source_code: str
    source_name: str
    source_type: SourceType
    bound_layer: BoundLayer
    quotation: str | None
    reference: str | None
    note: str | None
    fact_eligible: bool


class SourceTypeMeta(BaseModel):
    """来源类型说明，供编辑器下拉使用。"""

    code: str
    name_zh: str
    fact_eligible: bool
