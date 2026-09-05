"""Phase 2 基础设施 API 测试。"""

import pytest
from httpx import AsyncClient

from backend.core.ids import EntityPrefix, new_id
from backend.core.schema_version import CURRENT_SCHEMA_VERSION


@pytest.mark.asyncio
async def test_health_and_meta(client: AsyncClient) -> None:
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["data"]["schema_version"] == CURRENT_SCHEMA_VERSION

    meta = await client.get("/api/v1/meta")
    assert meta.status_code == 200
    body = meta.json()["data"]
    assert body["schema_version"] == CURRENT_SCHEMA_VERSION
    assert body["alembic_script_head"] == "0005_phase5"
    assert body["id_prefixes"]["project"] == "prj"
    assert body["id_prefixes"]["character"] == "chr"
    assert body["id_prefixes"]["source"] == "src"
    assert body["id_prefixes"]["relationship"] == "rel"
    assert body["id_prefixes"]["skill"] == "skl"
    assert any(item["code"] == "command" for item in body["skill_types"])
    assert any(item["code"] == "modify_stat" for item in body["effect_types"])
    assert any(item["code"] == "literary" and item["fact_eligible"] is False for item in body["source_types"])
    assert any(item["code"] == "sworn" and item["symmetric"] is True for item in body["relationship_types"])
    assert any(item["code"] == "ruler_subject" and item["symmetric"] is False for item in body["relationship_types"])


@pytest.mark.asyncio
async def test_invalid_project_id_returns_400(client: AsyncClient) -> None:
    response = await client.get("/api/v1/projects/not-a-valid-id")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_id"


@pytest.mark.asyncio
async def test_missing_project_with_valid_id_returns_404(client: AsyncClient) -> None:
    missing_id = new_id(EntityPrefix.PROJECT)
    response = await client.get(f"/api/v1/projects/{missing_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_create_project_assigns_prefixed_id_and_code(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "东汉末年", "code": "han_end"})
    assert created.status_code == 201
    project = created.json()["data"]
    assert project["id"].startswith("prj_")
    assert project["code"] == "han_end"
    assert project["schema_version"] == CURRENT_SCHEMA_VERSION

    duplicate = await client.post("/api/v1/projects", json={"name": "重复", "code": "han_end"})
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_update_project_keeps_code(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "草稿", "code": "draft_proj"})
    project_id = created.json()["data"]["id"]
    updated = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "正式项目", "description": "更新后的描述", "target_start_year": 184, "target_end_year": 280},
    )
    assert updated.status_code == 200
    body = updated.json()["data"]
    assert body["name"] == "正式项目"
    assert body["code"] == "draft_proj"
    assert body["content_version"] == 2
    assert body["target_start_year"] == 184
