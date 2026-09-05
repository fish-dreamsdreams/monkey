"""人物 Schema。历史事实与游戏设定在请求体中显式分栏。"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Gender(str, Enum):
    """性别。未知用于史料不足的情况。"""

    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class CharacterBaseInfo(BaseModel):
    """人物基础身份（可与历史记载对应，但不含战斗数值）。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    courtesy_name: str | None = Field(default=None, max_length=50)
    gender: Gender = Gender.UNKNOWN
    birth_year: int | None = Field(default=None, ge=-500, le=3000)
    death_year: int | None = Field(default=None, ge=-500, le=3000)
    birthplace: str | None = Field(default=None, max_length=100)
    ethnicity: str | None = Field(default=None, max_length=50)
    identity: str | None = Field(default=None, max_length=100)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class CharacterHistoricalData(BaseModel):
    """历史事实。不得写入生命值、武力等游戏数值。"""

    biography: str | None = None
    family_background: str | None = None
    life_experience: str | None = None
    achievements: str | None = None
    historical_evaluation: str | None = None


class CharacterGameData(BaseModel):
    """游戏设定。可因平衡性调整，不得回写历史表。"""

    force: int = Field(default=50, ge=0, le=100, description="武力")
    intelligence: int = Field(default=50, ge=0, le=100, description="智力")
    politics: int = Field(default=50, ge=0, le=100, description="政治")
    charisma: int = Field(default=50, ge=0, le=100, description="魅力")
    leadership: int = Field(default=50, ge=0, le=100, description="统率")
    stamina: int = Field(default=50, ge=0, le=100, description="体力")
    morale: int = Field(default=50, ge=0, le=100, description="士气")
    mobility: int = Field(default=50, ge=0, le=100, description="移动能力")
    personality_tag_codes: list[str] = Field(default_factory=list)
    attribute_version: str = Field(default="default", max_length=50)


class CharacterCreate(BaseModel):
    """创建人物：基础信息 + 历史事实 + 游戏设定。"""

    base: CharacterBaseInfo
    historical: CharacterHistoricalData = Field(default_factory=CharacterHistoricalData)
    game: CharacterGameData = Field(default_factory=CharacterGameData)


class CharacterUpdate(BaseModel):
    """全量更新人物。历史栏与游戏栏仍然分离。"""

    base: CharacterBaseInfo
    historical: CharacterHistoricalData = Field(default_factory=CharacterHistoricalData)
    game: CharacterGameData = Field(default_factory=CharacterGameData)


class PersonalityTagRead(BaseModel):
    """性格标签。"""

    id: str
    code: str
    name: str
    is_system: bool

    model_config = {"from_attributes": True}


class CharacterSummary(BaseModel):
    """人物列表摘要。"""

    id: str
    code: str
    name: str
    courtesy_name: str | None
    gender: Gender
    birth_year: int | None
    death_year: int | None
    identity: str | None


class CharacterRead(BaseModel):
    """人物详情，历史与游戏分栏返回。"""

    id: str
    project_id: str
    base: CharacterBaseInfo
    historical: CharacterHistoricalData
    game: CharacterGameData
    personalities: list[PersonalityTagRead]
    created_at: datetime
    updated_at: datetime
