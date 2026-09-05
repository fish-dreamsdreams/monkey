"""Phase 6 城池与势力测试。归属按时序派生，不预置魏蜀吴。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ConflictError
from backend.domain.faction_rules import assert_no_overlap
from tests.test_characters_api import LIU_BEI, _create_project

CHENGDU = {
    "code": "chengdu",
    "name": "成都",
    "coord_x": 120,
    "coord_y": 80,
    "historical": {
        "historical_name": "成都",
        "founded_year": -311,
        "description": "益州治所。",
    },
    "game": {"population": 280000, "military": 70, "economy": 80, "defense": 75},
}

LEFT_GENERAL = {
    "code": "left_general",
    "name": "左将军领",
    "color": "#226622",
    "start_year": 184,
    "end_year": 221,
    "historical_description": "用户创建的刘备早期势力，不是预置蜀汉。",
}

CAO_FACTION = {
    "code": "minister_cao",
    "name": "曹司空府",
    "color": "#2244AA",
    "start_year": 196,
    "end_year": 220,
}


def test_overlapping_territory_is_conflict() -> None:
    with pytest.raises(ConflictError):
        assert_no_overlap([(214, 263)], 220, 230, "重叠")


async def _create_character(client: AsyncClient, project_id: str) -> str:
    response = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert response.status_code == 201
    return str(response.json()["data"]["id"])


@pytest.mark.asyncio
async def test_new_project_has_no_preset_three_kingdoms(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    factions = await client.get(f"/api/v1/projects/{project_id}/factions")
    assert factions.status_code == 200
    assert factions.json()["data"] == []
    assert factions.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_city_owner_is_derived_by_year(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    city = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    assert city.status_code == 201
    city_id = city.json()["data"]["id"]
    assert city_id.startswith("cty_")
    assert city.json()["data"]["owner"] is None
    assert city.json()["data"]["historical"]["founded_year"] == -311
    assert city.json()["data"]["game"]["economy"] == 80

    character_id = await _create_character(client, project_id)
    faction_payload = {**LEFT_GENERAL, "leader_character_id": character_id, "capital_city_id": city_id}
    faction = await client.post(f"/api/v1/projects/{project_id}/factions", json=faction_payload)
    assert faction.status_code == 201
    faction_id = faction.json()["data"]["id"]
    assert faction_id.startswith("fac_")
    assert faction.json()["data"]["leader"]["name"] == "刘备"
    assert faction.json()["data"]["capital"]["name"] == "成都"

    member = await client.post(
        f"/api/v1/projects/{project_id}/factions/{faction_id}/members",
        json={"character_id": character_id, "role": "leader", "start_year": 184, "end_year": 221},
    )
    assert member.status_code == 201
    assert member.json()["data"]["id"].startswith("fmb_")

    territory = await client.post(
        f"/api/v1/projects/{project_id}/factions/{faction_id}/territories",
        json={"city_id": city_id, "start_year": 214, "end_year": 221, "note": "刘备入成都"},
    )
    assert territory.status_code == 201
    assert territory.json()["data"]["id"].startswith("ftr_")

    before = await client.get(f"/api/v1/projects/{project_id}/cities/{city_id}", params={"at_year": 208})
    assert before.json()["data"]["owner"] is None

    after = await client.get(f"/api/v1/projects/{project_id}/cities/{city_id}", params={"at_year": 215})
    assert after.json()["data"]["owner"]["code"] == "left_general"

    view = await client.get(f"/api/v1/projects/{project_id}/year-view", params={"year": 215})
    assert view.status_code == 200
    body = view.json()["data"]
    assert body["year"] == 215
    owned = next(item for item in body["cities"] if item["id"] == city_id)
    assert owned["owner"]["name"] == "左将军领"
    faction_view = next(item for item in body["factions"] if item["id"] == faction_id)
    assert any(item["character"]["name"] == "刘备" for item in faction_view["members"])
    assert any(item["name"] == "成都" for item in faction_view["cities"])


@pytest.mark.asyncio
async def test_character_cannot_join_two_factions_in_same_years(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    character_id = await _create_character(client, project_id)
    first = await client.post(f"/api/v1/projects/{project_id}/factions", json=LEFT_GENERAL)
    second = await client.post(f"/api/v1/projects/{project_id}/factions", json=CAO_FACTION)
    first_id = first.json()["data"]["id"]
    second_id = second.json()["data"]["id"]
    ok = await client.post(
        f"/api/v1/projects/{project_id}/factions/{first_id}/members",
        json={"character_id": character_id, "role": "leader", "start_year": 184, "end_year": 221},
    )
    assert ok.status_code == 201
    conflict = await client.post(
        f"/api/v1/projects/{project_id}/factions/{second_id}/members",
        json={"character_id": character_id, "role": "officer", "start_year": 200, "end_year": 208},
    )
    assert conflict.status_code == 409


@pytest.mark.asyncio
async def test_city_cannot_belong_to_two_factions_in_same_years(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    city = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    city_id = city.json()["data"]["id"]
    first = await client.post(f"/api/v1/projects/{project_id}/factions", json=LEFT_GENERAL)
    second = await client.post(
        f"/api/v1/projects/{project_id}/factions",
        json={"code": "yi_province", "name": "益州牧", "start_year": 188, "end_year": 214},
    )
    first_id = first.json()["data"]["id"]
    second_id = second.json()["data"]["id"]
    ok = await client.post(
        f"/api/v1/projects/{project_id}/factions/{second_id}/territories",
        json={"city_id": city_id, "start_year": 188, "end_year": 214},
    )
    assert ok.status_code == 201
    conflict = await client.post(
        f"/api/v1/projects/{project_id}/factions/{first_id}/territories",
        json={"city_id": city_id, "start_year": 214, "end_year": 221},
    )
    assert conflict.status_code == 409


@pytest.mark.asyncio
async def test_territory_must_fit_city_lifespan(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    city = await client.post(
        f"/api/v1/projects/{project_id}/cities",
        json={
            "code": "luoyang",
            "name": "洛阳",
            "historical": {"founded_year": 100, "destroyed_year": 190},
        },
    )
    city_id = city.json()["data"]["id"]
    faction = await client.post(f"/api/v1/projects/{project_id}/factions", json=CAO_FACTION)
    faction_id = faction.json()["data"]["id"]
    too_late = await client.post(
        f"/api/v1/projects/{project_id}/factions/{faction_id}/territories",
        json={"city_id": city_id, "start_year": 196, "end_year": 200},
    )
    assert too_late.status_code == 400
