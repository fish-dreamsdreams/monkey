"""项目导入导出 API 测试。"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from backend.domain.export_rules import checksum_payload
from backend.core.schema_version import CURRENT_SCHEMA_VERSION

LIU_BEI = {
    "base": {
        "code": "chr_liu_bei",
        "name": "刘备",
        "courtesy_name": "玄德",
        "gender": "male",
        "birth_year": 161,
        "death_year": 223,
    },
    "historical": {"biography": "蜀汉开国皇帝。"},
    "game": {"force": 72, "intelligence": 80, "charisma": 95},
}


async def _create_project(client: AsyncClient) -> str:
    response = await client.post("/api/v1/projects", json={"name": "导出测试", "code": "proj_export_demo"})
    assert response.status_code == 201
    return str(response.json()["data"]["id"])


@pytest.mark.asyncio
async def test_export_empty_project_writes_package(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    exported = await client.post(f"/api/v1/projects/{project_id}/export")
    assert exported.status_code == 200
    body = exported.json()["data"]
    package = body["package"]
    assert package["manifest"]["schema_version"] == CURRENT_SCHEMA_VERSION
    assert "quests.json" not in package["manifest"]["files"]
    assert "timeline.json" not in package["manifest"]["files"]
    assert package["manifest"]["files"]["characters.json"] == checksum_payload(package["characters"])
    export_dir = Path(body["export_dir"])
    assert (export_dir / "manifest.json").is_file()
    assert (export_dir / "characters.json").is_file()


@pytest.mark.asyncio
async def test_export_blocked_when_story_invalid(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    story = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "sty_broken", "name": "残缺剧情", "layer": "literary"},
    )
    assert story.status_code == 201
    blocked = await client.post(f"/api/v1/projects/{project_id}/export")
    assert blocked.status_code == 409
    error = blocked.json()["error"]
    assert error["code"] == "export_blocked"
    assert error["details"]


@pytest.mark.asyncio
async def test_round_trip_character_import(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert created.status_code == 201
    exported = await client.post(f"/api/v1/projects/{project_id}/export")
    assert exported.status_code == 200
    package = exported.json()["data"]["package"]
    imported = await client.post("/api/v1/projects/import", json=package)
    assert imported.status_code == 201
    new_id = imported.json()["data"]["id"]
    assert new_id != project_id
    listing = await client.get(f"/api/v1/projects/{new_id}/characters")
    assert listing.status_code == 200
    names = {item["name"] for item in listing.json()["data"]}
    assert "刘备" in names


@pytest.mark.asyncio
async def test_import_rejects_unsupported_schema(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    exported = await client.post(f"/api/v1/projects/{project_id}/export")
    package = exported.json()["data"]["package"]
    package["manifest"]["schema_version"] = "99.0.0"
    rejected = await client.post("/api/v1/projects/import", json=package)
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "unsupported_schema"


@pytest.mark.asyncio
async def test_import_rejects_tampered_checksum(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    exported = await client.post(f"/api/v1/projects/{project_id}/export")
    package = exported.json()["data"]["package"]
    package["characters"][0]["base"]["name"] = "假刘备"
    rejected = await client.post("/api/v1/projects/import", json=package)
    assert rejected.status_code == 400
    assert rejected.json()["error"]["details"][0]["field"] == "files"


@pytest.mark.asyncio
async def test_save_snapshot_without_validation_and_open(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    story = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "sty_broken", "name": "残缺剧情", "layer": "literary"},
    )
    assert story.status_code == 201
    blocked = await client.post(f"/api/v1/projects/{project_id}/export")
    assert blocked.status_code == 409

    saved = await client.post(f"/api/v1/projects/{project_id}/save")
    assert saved.status_code == 200
    snapshot_dir = saved.json()["data"]["snapshot_dir"]
    assert Path(snapshot_dir).joinpath("manifest.json").is_file()

    opened = await client.post("/api/v1/projects/open", json={"snapshot_dir": snapshot_dir})
    assert opened.status_code == 201
    new_id = opened.json()["data"]["id"]
    assert new_id != project_id
    listing = await client.get(f"/api/v1/projects/{new_id}/characters")
    names = {item["name"] for item in listing.json()["data"]}
    assert "刘备" in names
