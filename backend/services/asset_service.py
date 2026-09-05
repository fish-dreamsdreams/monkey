"""资源管理服务。

职责：资源入库、路径存在性、checksum、人物/技能/城池/地图绑定。不渲染预览，不加载 3D。
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.core.paths import project_assets_dir
from backend.domain.asset_rules import (
    ICON_TYPES,
    MAP_PREVIEW_TYPES,
    PORTRAIT_TYPES,
    MeshFormat,
    ResourceType,
    normalize_asset_path,
    require_existing_file,
    resolve_asset_file,
    validate_bind_type,
    validate_checksum,
    validate_model_extension,
)
from backend.models.asset import ModelAsset, Resource
from backend.models.character import Character
from backend.repositories.asset_repository import AssetRepository
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.map_repository import MapRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.skill_repository import SkillRepository
from backend.schemas.asset import (
    CharacterPresentationRead,
    CharacterPresentationWrite,
    ModelAssetRead,
    ModelAssetWrite,
    ResourceRead,
    ResourceRef,
    ResourceWrite,
)

MAX_INGEST_BYTES = 2 * 1024 * 1024


class AssetService:
    """资源用例编排。"""

    def __init__(
        self,
        assets: AssetRepository,
        characters: CharacterRepository,
        skills: SkillRepository,
        cities: CityRepository,
        maps: MapRepository,
        projects: ProjectRepository,
    ) -> None:
        self._assets = assets
        self._characters = characters
        self._skills = skills
        self._cities = cities
        self._maps = maps
        self._projects = projects

    async def create(self, project_id: str, payload: ResourceWrite) -> ResourceRead:
        """登记资源。可选写入文件内容，然后校验路径存在。"""
        await self._require_project(project_id)
        if await self._assets.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"资源 code 已存在: {payload.code}")
        relative = normalize_asset_path(payload.path)
        preview = normalize_asset_path(payload.preview_path) if payload.preview_path else None
        payload_model = payload.model
        if payload.resource_type == ResourceType.MODEL and payload_model is None:
            payload_model = ModelAssetWrite()
        validate_model_extension(payload.resource_type, payload_model is not None)

        root = project_assets_dir(project_id)
        full_path = resolve_asset_file(root, relative)
        if payload.content_base64 is not None:
            self._write_ingest(full_path, payload.content_base64)
        require_existing_file(full_path)
        if preview is not None:
            require_existing_file(resolve_asset_file(root, preview))

        data = full_path.read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        validate_checksum(checksum, payload.checksum)

        resource = Resource(
            id=new_id(EntityPrefix.RESOURCE),
            project_id=project_id,
            code=payload.code,
            name=payload.name.strip(),
            resource_type=payload.resource_type.value,
            path=relative,
            checksum=checksum,
            byte_size=len(data),
            mime_type=payload.mime_type,
            preview_path=preview,
            note=payload.note,
        )
        if payload.resource_type == ResourceType.MODEL and payload_model is not None:
            resource.model_asset = ModelAsset(
                id=new_id(EntityPrefix.MODEL_ASSET),
                resource_id=resource.id,
                mesh_format=payload_model.mesh_format.value,
                lod_count=payload_model.lod_count,
                animation_set_note=payload_model.animation_set_note,
                skeleton_note=payload_model.skeleton_note,
            )
        await self._assets.add(resource)
        await self._bump(project_id)
        saved = await self._assets.get(project_id, resource.id)
        if saved is None:
            raise NotFoundError("资源创建后读取失败")
        return self._to_read(saved, root)

    async def upload(
        self,
        project_id: str,
        *,
        code: str,
        name: str,
        resource_type: ResourceType,
        filename: str,
        content: bytes,
        path: str | None = None,
        checksum: str | None = None,
        mime_type: str | None = None,
    ) -> ResourceRead:
        """接收上传的二进制并登记为资源。"""
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise ValidationError("文件名不合法", field="file")
        if not content:
            raise ValidationError("上传文件不能为空", field="file")
        relative = path or f"uploads/{safe_name}"
        encoded = base64.b64encode(content).decode("ascii")
        return await self.create(
            project_id,
            ResourceWrite(
                code=code,
                name=name,
                resource_type=resource_type,
                path=relative,
                checksum=checksum,
                mime_type=mime_type,
                content_base64=encoded,
            ),
        )

    async def get(self, project_id: str, resource_id: str) -> ResourceRead:
        """获取资源并复查文件是否仍在。"""
        resource = await self._require_resource(project_id, resource_id)
        return self._to_read(resource, project_assets_dir(project_id))

    async def list_resources(self, project_id: str) -> list[ResourceRead]:
        """列出项目资源。"""
        await self._require_project(project_id)
        root = project_assets_dir(project_id)
        return [self._to_read(item, root) for item in await self._assets.list_by_project(project_id)]

    async def delete(self, project_id: str, resource_id: str) -> None:
        """删除资源登记；文件若在 assets 下则一并删除。"""
        resource = await self._require_resource(project_id, resource_id)
        root = project_assets_dir(project_id)
        try:
            full = resolve_asset_file(root, resource.path)
        except ValidationError:
            full = None
        await self._assets.delete(resource)
        await self._bump(project_id)
        if full is not None and full.is_file():
            full.unlink()

    async def bind_character_presentation(
        self,
        project_id: str,
        character_id: str,
        payload: CharacterPresentationWrite,
    ) -> CharacterPresentationRead:
        """绑定人物头像与模型。只存资源 ID。"""
        character = await self._require_character(project_id, character_id)
        portrait = await self._resolve_bind(
            project_id,
            payload.portrait_id,
            PORTRAIT_TYPES,
            field="portrait_id",
        )
        model = await self._resolve_bind(
            project_id,
            payload.model_id,
            frozenset({ResourceType.MODEL}),
            field="model_id",
        )
        character.portrait_asset_id = portrait.id if portrait else None
        character.model_asset_id = model.id if model else None
        character.portrait_asset = portrait
        character.model_asset = model
        await self._bump(project_id)
        return CharacterPresentationRead(
            portrait=to_resource_ref(portrait),
            model=to_resource_ref(model),
        )

    async def bind_skill_icon(self, project_id: str, skill_id: str, resource_id: str | None) -> ResourceRef | None:
        """绑定技能图标。"""
        skill = await self._skills.get(project_id, skill_id)
        if skill is None:
            raise NotFoundError("技能不存在")
        resource = await self._resolve_bind(project_id, resource_id, ICON_TYPES, field="resource_id")
        skill.icon_asset_id = resource.id if resource else None
        await self._bump(project_id)
        return to_resource_ref(resource)

    async def bind_city_icon(self, project_id: str, city_id: str, resource_id: str | None) -> ResourceRef | None:
        """绑定城池图标。"""
        city = await self._cities.get(project_id, city_id)
        if city is None:
            raise NotFoundError("城池不存在")
        resource = await self._resolve_bind(project_id, resource_id, ICON_TYPES, field="resource_id")
        city.icon_asset_id = resource.id if resource else None
        await self._bump(project_id)
        return to_resource_ref(resource)

    async def bind_map_preview(self, project_id: str, map_id: str, resource_id: str | None) -> ResourceRef | None:
        """绑定地图预览图。"""
        game_map = await self._maps.get(project_id, map_id)
        if game_map is None:
            raise NotFoundError("地图不存在")
        resource = await self._resolve_bind(project_id, resource_id, MAP_PREVIEW_TYPES, field="resource_id")
        game_map.preview_asset_id = resource.id if resource else None
        await self._bump(project_id)
        return to_resource_ref(resource)

    async def _resolve_bind(
        self,
        project_id: str,
        resource_id: str | None,
        allowed: frozenset[ResourceType],
        *,
        field: str,
    ) -> Resource | None:
        if resource_id is None:
            return None
        require_id(resource_id, EntityPrefix.RESOURCE, field=field)
        resource = await self._assets.get(project_id, resource_id)
        if resource is None:
            raise NotFoundError("资源不存在")
        resource_type = ResourceType(resource.resource_type)
        validate_bind_type(resource_type, allowed, field=field)
        root = project_assets_dir(project_id)
        require_existing_file(resolve_asset_file(root, resource.path))
        return resource

    def _write_ingest(self, full_path: Path, content_base64: str) -> None:
        try:
            raw = base64.b64decode(content_base64, validate=True)
        except Exception as exc:
            raise ValidationError("content_base64 不是合法 Base64", field="content_base64") from exc
        if not raw:
            raise ValidationError("资源内容不能为空", field="content_base64")
        if len(raw) > MAX_INGEST_BYTES:
            raise ValidationError("资源内容过大", field="content_base64")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(raw)

    def _to_read(self, resource: Resource, root: Path) -> ResourceRead:
        exists = False
        checksum_ok = False
        try:
            full = resolve_asset_file(root, resource.path)
            exists = full.is_file()
            if exists:
                checksum_ok = hashlib.sha256(full.read_bytes()).hexdigest() == resource.checksum
        except ValidationError:
            exists = False
        model = None
        if resource.model_asset is not None:
            model = ModelAssetRead(
                id=resource.model_asset.id,
                mesh_format=MeshFormat(resource.model_asset.mesh_format),
                lod_count=resource.model_asset.lod_count,
                animation_set_note=resource.model_asset.animation_set_note,
                skeleton_note=resource.model_asset.skeleton_note,
            )
        return ResourceRead(
            id=resource.id,
            project_id=resource.project_id,
            code=resource.code,
            name=resource.name,
            resource_type=ResourceType(resource.resource_type),
            path=resource.path,
            checksum=resource.checksum,
            byte_size=resource.byte_size,
            mime_type=resource.mime_type,
            preview_path=resource.preview_path,
            note=resource.note,
            exists=exists,
            checksum_ok=checksum_ok,
            model=model,
        )

    async def _require_resource(self, project_id: str, resource_id: str) -> Resource:
        await self._require_project(project_id)
        resource = await self._assets.get(project_id, resource_id)
        if resource is None:
            raise NotFoundError("资源不存在")
        return resource

    async def _require_character(self, project_id: str, character_id: str) -> Character:
        await self._require_project(project_id)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        return character

    async def _require_project(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)


def to_resource_ref(resource: Resource | None) -> ResourceRef | None:
    """把资源压成引用，不含 checksum 与绝对路径。"""
    if resource is None:
        return None
    return ResourceRef(
        id=resource.id,
        code=resource.code,
        name=resource.name,
        resource_type=ResourceType(resource.resource_type),
        path=resource.path,
    )


def presentation_from_character(character: Character) -> CharacterPresentationRead:
    """从人物聚合读取展示绑定。"""
    return CharacterPresentationRead(
        portrait=to_resource_ref(character.portrait_asset),
        model=to_resource_ref(character.model_asset),
    )
