"""项目 Schema。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from backend.schemas.relationship import RelationshipTypeMeta
from backend.schemas.skill import SkillTypeMeta
from backend.schemas.source import SourceTypeMeta


class ProjectCreate(BaseModel):
    """创建内容项目。code 可省略，服务端会生成。"""

    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = None
    target_start_year: int | None = Field(default=None, ge=-500, le=3000)
    target_end_year: int | None = Field(default=None, ge=-500, le=3000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value


class ProjectUpdate(BaseModel):
    """更新项目元数据。code 与 schema_version 不可改。"""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    target_start_year: int | None = Field(default=None, ge=-500, le=3000)
    target_end_year: int | None = Field(default=None, ge=-500, le=3000)


class ProjectRead(BaseModel):
    """项目详情。"""

    id: str
    code: str
    name: str
    description: str | None
    schema_version: str
    content_version: int
    target_start_year: int | None
    target_end_year: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EditorMetaRead(BaseModel):
    """编辑器与导出契约元信息，不依赖当前打开的项目。"""

    api_version: str
    schema_version: str
    supported_schema_versions: list[str]
    alembic_script_head: str
    id_prefixes: dict[str, str]
    source_types: list[SourceTypeMeta]
    relationship_types: list[RelationshipTypeMeta]
    skill_types: list[SkillTypeMeta]
    effect_types: list[SkillTypeMeta]
