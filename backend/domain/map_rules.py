"""地图领域规则。

职责：校验网格边界、地形类型与矢量地物几何。编辑器只存数据，不渲染 Canvas。
"""

from enum import Enum

from backend.core.exceptions import ValidationError

MIN_MAP_SIZE = 4
MAX_MAP_SIZE = 256
MAX_TERRAIN_PATCH = 4096


class TerrainType(str, Enum):
    """地块地形。缺省格子由地图 default_terrain 解释，通常为平原。"""

    PLAIN = "plain"
    FOREST = "forest"
    HILL = "hill"
    MOUNTAIN = "mountain"
    WATER = "water"
    SWAMP = "swamp"
    DESERT = "desert"
    PASS = "pass"
    FARMLAND = "farmland"
    URBAN = "urban"


TERRAIN_TYPE_LABELS_ZH: dict[TerrainType, str] = {
    TerrainType.PLAIN: "平原",
    TerrainType.FOREST: "森林",
    TerrainType.HILL: "丘陵",
    TerrainType.MOUNTAIN: "山地",
    TerrainType.WATER: "水域",
    TerrainType.SWAMP: "沼泽",
    TerrainType.DESERT: "荒漠",
    TerrainType.PASS: "关隘",
    TerrainType.FARMLAND: "农田",
    TerrainType.URBAN: "城郭",
}


class MapFeatureType(str, Enum):
    """矢量地物。区域/山脉为面，道路/河流为线。"""

    REGION = "region"
    ROAD = "road"
    RIVER = "river"
    MOUNTAIN = "mountain"


MAP_FEATURE_TYPE_LABELS_ZH: dict[MapFeatureType, str] = {
    MapFeatureType.REGION: "区域",
    MapFeatureType.ROAD: "道路",
    MapFeatureType.RIVER: "河流",
    MapFeatureType.MOUNTAIN: "山脉",
}

POLYGON_FEATURE_TYPES: frozenset[MapFeatureType] = frozenset(
    {MapFeatureType.REGION, MapFeatureType.MOUNTAIN}
)


def validate_map_size(width: int, height: int) -> None:
    """地图宽高必须在编辑器可管理范围内。"""
    if width < MIN_MAP_SIZE or width > MAX_MAP_SIZE:
        raise ValidationError(f"地图宽度必须介于 {MIN_MAP_SIZE} 与 {MAX_MAP_SIZE} 之间", field="width")
    if height < MIN_MAP_SIZE or height > MAX_MAP_SIZE:
        raise ValidationError(f"地图高度必须介于 {MIN_MAP_SIZE} 与 {MAX_MAP_SIZE} 之间", field="height")


def validate_cell_in_bounds(x: int, y: int, width: int, height: int) -> None:
    """地形格子坐标为整数且落在 [0, width) × [0, height)。"""
    if x < 0 or x >= width:
        raise ValidationError("地块 x 超出地图宽度", field="x")
    if y < 0 or y >= height:
        raise ValidationError("地块 y 超出地图高度", field="y")


def validate_city_in_bounds(x: int, y: int, width: int, height: int) -> None:
    """城池锚点使用整数格心，必须落在地图内。"""
    if x < 0 or x >= width:
        raise ValidationError("城池坐标超出地图宽度", field="coord_x")
    if y < 0 or y >= height:
        raise ValidationError("城池坐标超出地图高度", field="coord_y")


def validate_point_in_bounds(x: float, y: float, width: int, height: int) -> None:
    """矢量点允许落在格线上，范围 [0, width] × [0, height]。"""
    if x < 0 or x > width:
        raise ValidationError("地物坐标超出地图宽度", field="x")
    if y < 0 or y > height:
        raise ValidationError("地物坐标超出地图高度", field="y")


def min_points_for(feature_type: MapFeatureType) -> int:
    """线至少两点，面至少三点。"""
    return 3 if feature_type in POLYGON_FEATURE_TYPES else 2


def validate_feature_points(
    feature_type: MapFeatureType,
    points: list[tuple[float, float]],
    width: int,
    height: int,
) -> None:
    """校验地物点数与边界。"""
    required = min_points_for(feature_type)
    if len(points) < required:
        kind = "面" if required == 3 else "线"
        raise ValidationError(f"{kind}状地物至少需要 {required} 个点", field="points")
    for x, y in points:
        validate_point_in_bounds(x, y, width, height)


def validate_terrain_patch_size(count: int) -> None:
    """分块提交地形，避免一次上传整个网格。"""
    if count < 1:
        raise ValidationError("地形补丁不能为空", field="cells")
    if count > MAX_TERRAIN_PATCH:
        raise ValidationError(f"单次地形补丁最多 {MAX_TERRAIN_PATCH} 格", field="cells")
