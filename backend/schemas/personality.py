"""性格标签写入 Schema。"""

from pydantic import BaseModel, Field, field_validator


class PersonalityTagCreate(BaseModel):
    """新增自定义性格标签。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class PersonalityTagUpdate(BaseModel):
    """更新性格标签。code 不可改。"""

    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
