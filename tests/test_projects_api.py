"""项目 API 测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_seeds_personality_tags(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "东汉末年", "target_start_year": 184, "target_end_year": 280})
    assert created.status_code == 201
    project = created.json()["data"]
    assert project["schema_version"] == "1.12.0"
    assert project["content_version"] == 1
    assert project["id"].startswith("prj_")
    assert project["code"]

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


@pytest.mark.asyncio
async def test_update_and_delete_custom_personality_tag(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "标签改删"})
    project_id = created.json()["data"]["id"]
    tag = await client.post(
        f"/api/v1/projects/{project_id}/personality-tags",
        json={"code": "righteous", "name": "义气"},
    )
    tag_id = tag.json()["data"]["id"]
    updated = await client.put(
        f"/api/v1/projects/{project_id}/personality-tags/{tag_id}",
        json={"name": "仁义", "description": "自定义"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "仁义"

    deleted = await client.delete(f"/api/v1/projects/{project_id}/personality-tags/{tag_id}")
    assert deleted.status_code == 200
    listing = await client.get(f"/api/v1/projects/{project_id}/personality-tags")
    codes = {item["code"] for item in listing.json()["data"]}
    assert "righteous" not in codes

    system_id = next(item["id"] for item in listing.json()["data"] if item["is_system"])
    blocked = await client.delete(f"/api/v1/projects/{project_id}/personality-tags/{system_id}")
    assert blocked.status_code == 409


@pytest.mark.asyncio
async def test_delete_project_removes_it(client: AsyncClient) -> None:
    created = await client.post("/api/v1/projects", json={"name": "待删除"})
    project_id = created.json()["data"]["id"]
    deleted = await client.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 200
    missing = await client.get(f"/api/v1/projects/{project_id}")
    assert missing.status_code == 404
    listing = await client.get("/api/v1/projects")
    ids = {item["id"] for item in listing.json()["data"]}
    assert project_id not in ids
