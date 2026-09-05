"""Phase 10 资源与模型测试。路径必须存在，人物只引用资源 ID。"""

from __future__ import annotations

import base64
import hashlib

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.asset_rules import normalize_asset_path
from tests.test_characters_api import LIU_BEI, _create_project
from tests.test_cities_factions_api import CHENGDU
from tests.test_skills_api import EMPTY_FORT

PORTRAIT_BYTES = b"liu-bei-portrait"
MODEL_BYTES = b"liu-bei-gltf"
ICON_BYTES = b"empty-fort-icon"


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def test_reject_absolute_and_parent_paths() -> None:
    with pytest.raises(ValidationError):
        normalize_asset_path("../secret.png")
    with pytest.raises(ValidationError):
        normalize_asset_path("/tmp/portrait.png")
    with pytest.raises(ValidationError):
        normalize_asset_path("C:/portraits/liu_bei.png")
    assert normalize_asset_path("portraits\\liu_bei.png") == "portraits/liu_bei.png"


@pytest.mark.asyncio
async def test_register_portrait_requires_existing_file_and_checksum(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    missing = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_liu_bei_portrait",
            "name": "刘备头像",
            "resource_type": "portrait",
            "path": "portraits/missing.png",
        },
    )
    assert missing.status_code == 400

    created = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_liu_bei_portrait",
            "name": "刘备头像",
            "resource_type": "portrait",
            "path": "portraits/liu_bei.png",
            "content_base64": _b64(PORTRAIT_BYTES),
            "checksum": hashlib.sha256(PORTRAIT_BYTES).hexdigest(),
        },
    )
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["id"].startswith("res_")
    assert body["path"] == "portraits/liu_bei.png"
    assert body["exists"] is True
    assert body["checksum_ok"] is True
    assert body["model"] is None

    wrong = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_bad_checksum",
            "name": "错误校验",
            "resource_type": "portrait",
            "path": "portraits/bad.png",
            "content_base64": _b64(PORTRAIT_BYTES),
            "checksum": "0" * 64,
        },
    )
    assert wrong.status_code == 400


@pytest.mark.asyncio
async def test_bind_character_portrait_and_model_by_id_not_path(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    character = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = character.json()["data"]["id"]
    assert character.json()["data"]["presentation"]["portrait"] is None

    portrait = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_liu_bei_portrait",
            "name": "刘备头像",
            "resource_type": "portrait",
            "path": "portraits/liu_bei.png",
            "content_base64": _b64(PORTRAIT_BYTES),
        },
    )
    portrait_id = portrait.json()["data"]["id"]
    model = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_liu_bei_model",
            "name": "刘备模型",
            "resource_type": "model",
            "path": "models/liu_bei.gltf",
            "content_base64": _b64(MODEL_BYTES),
            "model": {"mesh_format": "gltf", "lod_count": 2},
        },
    )
    assert model.status_code == 201
    assert model.json()["data"]["model"]["mesh_format"] == "gltf"
    model_id = model.json()["data"]["id"]
    assert model_id.startswith("res_")
    assert model.json()["data"]["model"]["id"].startswith("mas_")

    rejected = await client.put(
        f"/api/v1/projects/{project_id}/characters/{character_id}/presentation",
        json={"portrait_id": model_id},
    )
    assert rejected.status_code == 400

    bound = await client.put(
        f"/api/v1/projects/{project_id}/characters/{character_id}/presentation",
        json={"portrait_id": portrait_id, "model_id": model_id},
    )
    assert bound.status_code == 200
    presentation = bound.json()["data"]
    assert presentation["portrait"]["id"] == portrait_id
    assert presentation["portrait"]["path"] == "portraits/liu_bei.png"
    assert presentation["model"]["id"] == model_id
    assert ":" not in presentation["portrait"]["path"]

    detail = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    body = detail.json()["data"]
    assert body["presentation"]["portrait"]["id"] == portrait_id
    assert body["presentation"]["model"]["id"] == model_id
    assert "portrait_asset_id" not in body["base"]
    assert "force" not in body["historical"]


@pytest.mark.asyncio
async def test_bind_skill_icon_and_city_icon(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    skill = await client.post(f"/api/v1/projects/{project_id}/skills", json=EMPTY_FORT)
    skill_id = skill.json()["data"]["id"]
    city = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    city_id = city.json()["data"]["id"]
    game_map = await client.post(
        f"/api/v1/projects/{project_id}/maps",
        json={"code": "han_land", "name": "汉末九州", "width": 20, "height": 16},
    )
    map_id = game_map.json()["data"]["id"]

    icon = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_empty_fort_icon",
            "name": "空城计图标",
            "resource_type": "icon",
            "path": "icons/empty_fort.png",
            "content_base64": _b64(ICON_BYTES),
        },
    )
    icon_id = icon.json()["data"]["id"]
    preview = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_map_preview",
            "name": "九州预览",
            "resource_type": "map_preview",
            "path": "maps/han_land.png",
            "content_base64": _b64(b"map-preview"),
        },
    )
    preview_id = preview.json()["data"]["id"]

    skill_bind = await client.put(
        f"/api/v1/projects/{project_id}/skills/{skill_id}/icon",
        json={"resource_id": icon_id},
    )
    assert skill_bind.status_code == 200
    assert skill_bind.json()["data"]["id"] == icon_id

    city_bind = await client.put(
        f"/api/v1/projects/{project_id}/cities/{city_id}/icon",
        json={"resource_id": icon_id},
    )
    assert city_bind.status_code == 200

    map_bind = await client.put(
        f"/api/v1/projects/{project_id}/maps/{map_id}/preview",
        json={"resource_id": preview_id},
    )
    assert map_bind.status_code == 200
    assert map_bind.json()["data"]["resource_type"] == "map_preview"

    portrait = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_wrong_type",
            "name": "头像不能当地图预览",
            "resource_type": "portrait",
            "path": "portraits/wrong.png",
            "content_base64": _b64(PORTRAIT_BYTES),
        },
    )
    wrong = await client.put(
        f"/api/v1/projects/{project_id}/maps/{map_id}/preview",
        json={"resource_id": portrait.json()["data"]["id"]},
    )
    assert wrong.status_code == 400
