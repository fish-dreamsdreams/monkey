"""Phase 8 历史事件测试。参与者必须活在事件当年。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.event_rules import validate_character_alive_in_year, validate_event_date
from tests.test_characters_api import LIU_BEI, _create_project
from tests.test_cities_factions_api import CHENGDU, LEFT_GENERAL


def test_dead_character_cannot_join_later_event() -> None:
    with pytest.raises(ValidationError):
        validate_character_alive_in_year(
            character_name="刘备",
            birth_year=161,
            death_year=223,
            event_year=230,
        )


def test_day_requires_month() -> None:
    with pytest.raises(ValidationError):
        validate_event_date(208, None, 12)


@pytest.mark.asyncio
async def test_create_battle_and_bind_living_participant(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    city = await client.post(f"/api/v1/projects/{project_id}/cities", json=CHENGDU)
    city_id = city.json()["data"]["id"]
    character = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = character.json()["data"]["id"]
    faction = await client.post(f"/api/v1/projects/{project_id}/factions", json=LEFT_GENERAL)
    faction_id = faction.json()["data"]["id"]

    created = await client.post(
        f"/api/v1/projects/{project_id}/events",
        json={
            "code": "battle_red_cliffs",
            "name": "赤壁之战",
            "event_type": "battle",
            "layer": "historical",
            "year": 208,
            "month": 12,
            "location_city_id": city_id,
            "description": "孙刘联军破曹。",
            "consequences": "曹操北还，三分雏形。仅作记录，不结算战斗。",
        },
    )
    assert created.status_code == 201
    event = created.json()["data"]
    assert event["id"].startswith("evt_")
    assert event["location"]["name"] == "成都"
    event_id = event["id"]

    cited = await client.post(
        f"/api/v1/projects/{project_id}/events/{event_id}/sources",
        json={"source_code": "sanguozhi", "reference": "武帝纪"},
    )
    assert cited.status_code == 201

    literary = await client.post(
        f"/api/v1/projects/{project_id}/events/{event_id}/sources",
        json={"source_code": "sanguoyanyi"},
    )
    assert literary.status_code == 400

    participant = await client.post(
        f"/api/v1/projects/{project_id}/events/{event_id}/participants",
        json={"character_id": character_id, "role": "commander"},
    )
    assert participant.status_code == 201
    assert participant.json()["data"]["id"].startswith("evp_")

    involved = await client.post(
        f"/api/v1/projects/{project_id}/events/{event_id}/factions",
        json={"faction_id": faction_id, "role": "involved"},
    )
    assert involved.status_code == 201

    listing = await client.get(f"/api/v1/projects/{project_id}/events", params={"year": 208})
    assert listing.json()["meta"]["total"] == 1
    assert listing.json()["data"][0]["participant_count"] == 1

    detail = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert "赤壁" not in (detail.json()["data"]["historical"]["biography"] or "")


@pytest.mark.asyncio
async def test_reject_dead_participant_and_destroyed_city(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    character = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = character.json()["data"]["id"]
    later = await client.post(
        f"/api/v1/projects/{project_id}/events",
        json={"code": "evt_too_late", "name": "身后之事", "year": 230, "event_type": "other"},
    )
    later_id = later.json()["data"]["id"]
    dead = await client.post(
        f"/api/v1/projects/{project_id}/events/{later_id}/participants",
        json={"character_id": character_id},
    )
    assert dead.status_code == 400

    city = await client.post(
        f"/api/v1/projects/{project_id}/cities",
        json={
            "code": "luoyang",
            "name": "洛阳",
            "historical": {"founded_year": 100, "destroyed_year": 190},
        },
    )
    city_id = city.json()["data"]["id"]
    located = await client.post(
        f"/api/v1/projects/{project_id}/events",
        json={
            "code": "after_sack",
            "name": "洛阳已毁",
            "year": 208,
            "location_city_id": city_id,
        },
    )
    assert located.status_code == 400


@pytest.mark.asyncio
async def test_literary_event_can_cite_yanyi(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(
        f"/api/v1/projects/{project_id}/events",
        json={
            "code": "empty_fort",
            "name": "空城计",
            "event_type": "other",
            "layer": "literary",
            "year": 228,
            "description": "演义情节，不得写入人物史实栏。",
        },
    )
    assert created.status_code == 201
    event_id = created.json()["data"]["id"]
    cited = await client.post(
        f"/api/v1/projects/{project_id}/events/{event_id}/sources",
        json={"source_code": "sanguoyanyi", "note": "文学演义"},
    )
    assert cited.status_code == 201
    assert cited.json()["data"]["id"].startswith("evs_")
    assert cited.json()["data"]["fact_eligible"] is False
