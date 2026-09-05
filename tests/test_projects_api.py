"""项目 API 测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_seeds_personality_tags(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "东汉末年", "target_start_year": 184, "target_end_year": 280})
    assert created.status_code == 201
    project = created.json()["data"]
    assert project["schema_version"] == "1.0.0"
    assert project["content_version"] == 1

    tags = await client.get(f"/api/v1/projects/{project['id']}/personality-tags")
    assert tags.status_code == 200
    codes = {item["code"] for item in tags.json()["data"]}
    assert {"brave", "loyal", "cunning", "calm"} <= codes
    assert len(codes) == 9


@pytest.mark.asyncio
async def test_create_custom_personality_tag(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "测试项目"})
    project_id = created.json()["data"]["id"]
    tag = await client.post(
        f"/api/v1/projects/{project_id}/personality-tags",
        json={"code": "righteous", "name": "义气"},
    )
    assert tag.status_code == 201
    assert tag.json()["data"]["is_system"] is False

    duplicate = await client.post(
        f"/api/v1/projects/{project_id}/personality-tags",
        json={"code": "righteous", "name": "义气"},
    )
    assert duplicate.status_code == 409
