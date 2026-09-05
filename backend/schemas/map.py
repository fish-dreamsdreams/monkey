"""地图 Schema。地形分块提交；地物只存点列，不渲染。"""

from pydantic import BaseModel, Field, field_validator

from backend.domain.map_rules import MapFeatureType, TerrainType
from backend.schemas.city import CityRef


class MapWrite(BaseModel):
    """创建或更新地图元数据。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    width: int = Field(ge=4, le=256)
    height: int = Field(ge=4, le=256)
    cell_size: int = Field(default=32, ge=8, le=128)
    default_terrain: TerrainType = TerrainType.PLAIN
    description: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class MapPoint(BaseModel):
    """地图空间点。单位为格子坐标，可带小数。"""

    x: float
    y: float


class TerrainCellPatch(BaseModel):
    """单格地形。terrain 为空表示删除覆盖、恢复默认。"""

    x: int = Field(ge=0, le=255)
    y: int = Field(ge=0, le=255)
    terrain: TerrainType | None = None


class TerrainPatchWrite(BaseModel):
    """分块更新地形。"""

    cells: list[TerrainCellPatch] = Field(min_length=1, max_length=4096)


class TerrainCellRead(BaseModel):
    """已覆盖的地形格。"""

    x: int
    y: int
    terrain: TerrainType


class MapFeatureWrite(BaseModel):
    """创建或更新矢量地物。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    feature_type: MapFeatureType
    points: list[MapPoint] = Field(min_length=2)
    note: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class MapFeatureRead(BaseModel):
    """矢量地物。"""

    id: str
    code: str
    name: str
    feature_type: MapFeatureType
    points: list[MapPoint]
    note: str | None


class MapCityPlace(BaseModel):
    """把已有城池挂到地图格子上。"""

    city_id: str = Field(min_length=36, max_length=36)
    coord_x: int = Field(ge=0, le=255)
    coord_y: int = Field(ge=0, le=255)


class MapCityRead(CityRef):
    """地图上的城池锚点。"""

    coord_x: int
    coord_y: int


class MapRead(BaseModel):
    """地图详情（不含完整地形网格）。"""

    id: str
    project_id: str
    code: str
    name: str
    width: int
    height: int
    cell_size: int
    default_terrain: TerrainType
    description: str | None
    terrain_cell_count: int
    cities: list[MapCityRead]
    features: list[MapFeatureRead]


class MapSummary(BaseModel):
    """地图列表项。"""

    id: str
    project_id: str
    code: str
    name: str
    width: int
    height: int
    cell_size: int
    default_terrain: TerrainType
    terrain_cell_count: int
    city_count: int
    feature_count: int


class TypeMeta(BaseModel):
    """类型说明。"""

    code: str
    name_zh: str
