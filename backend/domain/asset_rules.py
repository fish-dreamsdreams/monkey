"""资源路径与类型规则。

职责：校验相对路径、类型与模型扩展。不渲染预览，不加载 3D。
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from backend.core.exceptions import ValidationError

_WINDOWS_DRIVE = re.compile(r"^[a-zA-Z]:")
MAX_RELATIVE_PATH_LENGTH = 200


class ResourceType(str, Enum):
    """资源类型。人物头像与模型必须用对应类型，禁止把裸路径写进人物表。"""

    PORTRAIT = "portrait"
    ICON = "icon"
    TEXTURE = "texture"
    MODEL = "model"
    ANIMATION = "animation"
    AUDIO = "audio"
    MAP_PREVIEW = "map_preview"
    OTHER = "other"


RESOURCE_TYPE_LABELS_ZH: dict[ResourceType, str] = {
    ResourceType.PORTRAIT: "头像",
    ResourceType.ICON: "图标",
    ResourceType.TEXTURE: "贴图",
    ResourceType.MODEL: "模型",
    ResourceType.ANIMATION: "动画",
    ResourceType.AUDIO: "音频",
    ResourceType.MAP_PREVIEW: "地图预览",
    ResourceType.OTHER: "其他",
}


class MeshFormat(str, Enum):
    """模型网格格式。仅作元数据。"""

    GLTF = "gltf"
    GLB = "glb"
    FBX = "fbx"
    OBJ = "obj"
    VRM = "vrm"


MESH_FORMAT_LABELS_ZH: dict[MeshFormat, str] = {
    MeshFormat.GLTF: "glTF",
    MeshFormat.GLB: "GLB",
    MeshFormat.FBX: "FBX",
    MeshFormat.OBJ: "OBJ",
    MeshFormat.VRM: "VRM",
}

PORTRAIT_TYPES: frozenset[ResourceType] = frozenset({ResourceType.PORTRAIT})
ICON_TYPES: frozenset[ResourceType] = frozenset({ResourceType.ICON, ResourceType.PORTRAIT, ResourceType.TEXTURE})
MAP_PREVIEW_TYPES: frozenset[ResourceType] = frozenset({ResourceType.MAP_PREVIEW, ResourceType.TEXTURE, ResourceType.ICON})


def normalize_asset_path(path: str) -> str:
    """资源路径必须相对项目 assets 根，禁止绝对路径与 ..。"""
    raw = path.strip().replace("\\", "/")
    if not raw:
        raise ValidationError("资源路径不能为空", field="path")
    if len(raw) > MAX_RELATIVE_PATH_LENGTH:
        raise ValidationError("资源路径过长", field="path")
    if raw.startswith("/") or raw.startswith("~") or _WINDOWS_DRIVE.match(raw):
        raise ValidationError("资源路径必须是相对路径", field="path")
    parts = [part for part in raw.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in raw.split("/")):
        raise ValidationError("资源路径不能包含 .. 或为空", field="path")
    if any(":" in part for part in parts):
        raise ValidationError("资源路径含有非法字符", field="path")
    return "/".join(parts)


def resolve_asset_file(root: Path, relative_path: str) -> Path:
    """把相对路径解析到 assets 根下，并防止逃逸。"""
    normalized = normalize_asset_path(relative_path)
    root_resolved = root.resolve()
    full = (root_resolved / Path(*normalized.split("/"))).resolve()
    try:
        full.relative_to(root_resolved)
    except ValueError as exc:
        raise ValidationError("资源路径超出项目 assets 目录", field="path") from exc
    return full


def require_existing_file(full_path: Path) -> None:
    """路径必须指向已存在的普通文件。"""
    if not full_path.is_file():
        raise ValidationError("资源文件不存在", field="path")


def validate_checksum(actual: str, expected: str | None) -> None:
    """若调用方提供 checksum，必须与文件内容一致。"""
    if expected is None:
        return
    normalized = expected.strip().lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise ValidationError("checksum 必须是 64 位 sha256 十六进制", field="checksum")
    if normalized != actual:
        raise ValidationError("checksum 与文件内容不一致", field="checksum")


def validate_model_extension(resource_type: ResourceType, has_model: bool) -> None:
    """模型资源必须有 ModelAsset；非模型不得带模型扩展。"""
    if resource_type == ResourceType.MODEL and not has_model:
        raise ValidationError("模型资源必须填写模型扩展信息", field="model")
    if resource_type != ResourceType.MODEL and has_model:
        raise ValidationError("非模型资源不能带模型扩展信息", field="model")


def validate_bind_type(resource_type: ResourceType, allowed: frozenset[ResourceType], *, field: str) -> None:
    """绑定目标只接受匹配类型的资源。"""
    if resource_type not in allowed:
        raise ValidationError("资源类型与绑定目标不匹配", field=field)
