"""城池 Schema。历史描述与游戏数值分栏；归属不入库。"""

from pydantic import BaseModel, Field, field_validator


class CityHistoricalData(BaseModel):
    """城池史实。"""

    historical_name: str | None = Field(default=None, max_length=100)
    founded_year: int | None = Field(default=None, ge=-500, le=3000)
    destroyed_year: int | None = Field(default=None, ge=-500, le=3000)
    description: str | None = None


class CityGameData(BaseModel):
    """城池游戏数值，可因平衡性调整。"""

    population: int = Field(default=0, ge=0, le=10000000)
    military: int = Field(default=50, ge=0, le=100)
    economy: int = Field(default=50, ge=0, le=100)
    defense: int = Field(default=50, ge=0, le=100)


class CityWrite(BaseModel):
    """创建或更新城池。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    coord_x: int | None = Field(default=None, ge=-10000, le=10000)
    coord_y: int | None = Field(default=None, ge=-10000, le=10000)
    historical: CityHistoricalData = Field(default_factory=CityHistoricalData)
    game: CityGameData = Field(default_factory=CityGameData)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class FactionRef(BaseModel):
    """势力摘要。"""

    id: str
    code: str
    name: str
    color: str


class CityRef(BaseModel):
    """城池摘要。"""

    id: str
    code: str
    name: str


class CityRead(BaseModel):
    """城池详情。owner 仅在指定 at_year 时填充。"""

    id: str
    project_id: str
    code: str
    name: str
    coord_x: int | None
    coord_y: int | None
    historical: CityHistoricalData
    game: CityGameData
    owner: FactionRef | None = None
