"""势力与时序成员、领土 Schema。"""

from pydantic import BaseModel, Field, field_validator

from backend.domain.faction_rules import FactionMemberRole
from backend.schemas.city import CityRead, CityRef, FactionRef
from backend.schemas.relationship import CharacterRef


class FactionWrite(BaseModel):
    """创建或更新势力。不提供预置魏蜀吴。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#808080", pattern=r"^#[0-9A-Fa-f]{6}$")
    leader_character_id: str | None = Field(default=None, min_length=36, max_length=36)
    capital_city_id: str | None = Field(default=None, min_length=36, max_length=36)
    start_year: int | None = Field(default=None, ge=-500, le=3000)
    end_year: int | None = Field(default=None, ge=-500, le=3000)
    historical_description: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.upper()


class FactionRead(BaseModel):
    """势力详情。"""

    id: str
    project_id: str
    code: str
    name: str
    color: str
    leader: CharacterRef | None
    capital: CityRef | None
    start_year: int | None
    end_year: int | None
    historical_description: str | None


class FactionMemberWrite(BaseModel):
    """人物入势。"""

    character_id: str = Field(min_length=36, max_length=36)
    role: FactionMemberRole = FactionMemberRole.MEMBER
    start_year: int | None = Field(default=None, ge=-500, le=3000)
    end_year: int | None = Field(default=None, ge=-500, le=3000)
    note: str | None = None


class FactionMemberRead(BaseModel):
    """势力成员记录。"""

    id: str
    faction: FactionRef
    character: CharacterRef
    role: FactionMemberRole
    start_year: int | None
    end_year: int | None
    note: str | None


class FactionTerritoryWrite(BaseModel):
    """城池在某时段归属该势力。"""

    city_id: str = Field(min_length=36, max_length=36)
    start_year: int | None = Field(default=None, ge=-500, le=3000)
    end_year: int | None = Field(default=None, ge=-500, le=3000)
    note: str | None = None


class FactionTerritoryRead(BaseModel):
    """领土时段。"""

    id: str
    faction: FactionRef
    city: CityRef
    start_year: int | None
    end_year: int | None
    note: str | None


class CityYearRead(CityRead):
    """某年城池视图。"""

    pass


class FactionYearRead(FactionRead):
    """某年势力视图。"""

    members: list[FactionMemberRead]
    cities: list[CityRef]


class YearView(BaseModel):
    """项目在指定年份的派生世界视图。"""

    year: int
    cities: list[CityRead]
    factions: list[FactionYearRead]


class MemberRoleMeta(BaseModel):
    """成员角色说明。"""

    code: str
    name_zh: str
