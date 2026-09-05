"""项目 Schema。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """创建内容项目。"""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    target_start_year: int | None = Field(default=None, ge=-500, le=3000)
    target_end_year: int | None = Field(default=None, ge=-500, le=3000)


class ProjectRead(BaseModel):
    """项目详情。"""

    id: str
    name: str
    description: str | None
    schema_version: str
    content_version: int
    target_start_year: int | None
    target_end_year: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
