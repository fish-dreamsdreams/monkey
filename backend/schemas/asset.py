"""资源与模型 Schema。人物只引用资源 ID，不接受裸路径。"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from backend.domain.asset_rules import MeshFormat, ResourceType


class ModelAssetWrite(BaseModel):
    """模型扩展。仅元数据。"""

    mesh_format: MeshFormat = MeshFormat.GLTF
    lod_count: int = Field(default=1, ge=1, le=8)
    animation_set_note: str | None = None
    skeleton_note: str | None = None


class ResourceWrite(BaseModel):
    """登记资源。path 相对项目 assets；content_base64 可选，用于入库写文件。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    resource_type: ResourceType
    path: str = Field(min_length=1, max_length=200)
    checksum: str | None = Field(default=None, max_length=64)
    mime_type: str | None = Field(default=None, max_length=100)
    preview_path: str | None = Field(default=None, max_length=200)
    note: str | None = None
    content_base64: str | None = None
    model: ModelAssetWrite | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()


class ModelAssetRead(BaseModel):
    """模型扩展读模型。"""

    id: str
    mesh_format: MeshFormat
    lod_count: int
    animation_set_note: str | None
    skeleton_note: str | None


class ResourceRead(BaseModel):
    """资源详情。exists 表示当前磁盘上文件仍在。"""

    id: str
    project_id: str
    code: str
    name: str
    resource_type: ResourceType
    path: str
    checksum: str
    byte_size: int
    mime_type: str | None
    preview_path: str | None
    note: str | None
    exists: bool
    checksum_ok: bool
    model: ModelAssetRead | None = None


class ResourceRef(BaseModel):
    """实体上的资源引用。不含绝对路径。"""

    id: str
    code: str
    name: str
    resource_type: ResourceType
    path: str


class CharacterPresentationWrite(BaseModel):
    """人物展示绑定。只能填资源 ID。"""

    portrait_id: str | None = None
    model_id: str | None = None


class CharacterPresentationRead(BaseModel):
    """人物展示栏。与 historical / game 并列，不写入史实。"""

    portrait: ResourceRef | None = None
    model: ResourceRef | None = None


class ResourceBindWrite(BaseModel):
    """把资源绑到技能图标、城池图标或地图预览。null 表示解绑。"""

    resource_id: str | None = None
