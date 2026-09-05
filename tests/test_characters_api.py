"""人物 API 测试。"""

import pytest
from httpx import AsyncClient

LIU_BEI = {
    "base": {
        "code": "chr_liu_bei",
        "name": "刘备",
        "courtesy_name": "玄德",
        "gender": "male",
        "birth_year": 161,
        "death_year": 223,
        "birthplace": "涿郡涿县",
        "ethnicity": "汉",
        "identity": "蜀汉开国皇帝",
    },
    "historical": {
        "biography": "东汉末年幽州涿郡人，蜀汉开国皇帝。",
        "family_background": "汉景帝子中山靖王刘胜之后。",
        "life_experience": "参与镇压黄巾、三顾茅庐、赤壁战后入蜀。",
        "achievements": "建立蜀汉政权。",
        "historical_evaluation": "正史评价与演义形象需分开看待。",
    },
    "game": {
        "force": 72,
        "intelligence": 80,
        "politics": 85,
        "charisma": 95,
        "leadership": 86,
        "stamina": 78,
        "morale": 90,
        "mobility": 70,
        "personality_tag_codes": ["benevolent", "ambitious", "loyal"],
    },
}


async def _create_project(client: AsyncClient) -> str:
    response = await client.post("/api/v1/projects", json={"name": "三国内容库"})
    assert response.status_code == 201
    return str(response.json()["data"]["id"])


@pytest.mark.asyncio
async def test_create_and_get_character_splits_historical_and_game(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["id"].startswith("chr_")
    assert body["base"]["name"] == "刘备"
    assert body["base"]["courtesy_name"] == "玄德"
    assert "force" not in body["historical"]
    assert body["historical"]["biography"].startswith("东汉末年")
    assert body["game"]["force"] == 72
    assert body["game"]["charisma"] == 95
    assert set(body["game"]["personality_tag_codes"]) == {"benevolent", "ambitious", "loyal"}

    detail = await client.get(f"/api/v1/projects/{project_id}/characters/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["base"]["code"] == "chr_liu_bei"

    listing = await client.get(f"/api/v1/projects/{project_id}/characters")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] == 1
    assert listing.json()["data"][0]["name"] == "刘备"


@pytest.mark.asyncio
async def test_reject_birth_year_after_death_year(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    payload = {
        "base": {
            "code": "chr_invalid",
            "name": "错误人物",
            "gender": "unknown",
            "birth_year": 223,
            "death_year": 161,
        }
    }
    response = await client.post(f"/api/v1/projects/{project_id}/characters", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_reject_duplicate_character_code(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    first = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert first.status_code == 201
    second = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_update_game_data_does_not_drop_historical_fields(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = created.json()["data"]["id"]
    payload = {
        "base": LIU_BEI["base"],
        "historical": LIU_BEI["historical"],
        "game": {**LIU_BEI["game"], "force": 60, "personality_tag_codes": ["benevolent"]},
    }
    updated = await client.put(f"/api/v1/projects/{project_id}/characters/{character_id}", json=payload)
    assert updated.status_code == 200
    data = updated.json()["data"]
    assert data["game"]["force"] == 60
    assert data["historical"]["biography"] == LIU_BEI["historical"]["biography"]
    assert data["game"]["personality_tag_codes"] == ["benevolent"]


@pytest.mark.asyncio
async def test_unknown_personality_tag_is_rejected(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    payload = {
        "base": {"code": "chr_zhang", "name": "张飞", "gender": "male"},
        "game": {"personality_tag_codes": ["not_exist"]},
    }
    response = await client.post(f"/api/v1/projects/{project_id}/characters", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_character_id_returns_400(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.get(f"/api/v1/projects/{project_id}/characters/bad-id")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_id"


@pytest.mark.asyncio
async def test_delete_character(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = created.json()["data"]["id"]
    deleted = await client.delete(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert deleted.status_code == 200
    missing = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert missing.status_code == 404
