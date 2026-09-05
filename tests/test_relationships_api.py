"""Phase 4 人物关系测试。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.relationship_types import validate_not_self, years_overlap

from tests.test_characters_api import LIU_BEI, _create_project

GUAN_YU = {
    "base": {
        "code": "chr_guan_yu",
        "name": "关羽",
        "courtesy_name": "云长",
        "gender": "male",
        "birth_year": 160,
        "death_year": 220,
        "identity": "蜀汉前将军",
    }
}

ZHANG_FEI = {
    "base": {
        "code": "chr_zhang_fei",
        "name": "张飞",
        "courtesy_name": "益德",
        "gender": "male",
        "birth_year": 167,
        "death_year": 221,
    }
}

ZHUGE_LIANG = {
    "base": {
        "code": "chr_zhuge_liang",
        "name": "诸葛亮",
        "courtesy_name": "孔明",
        "gender": "male",
        "birth_year": 181,
        "death_year": 234,
        "identity": "蜀汉丞相",
    }
}


def test_reject_self_relationship() -> None:
    with pytest.raises(ValidationError):
        validate_not_self("chr_aaa", "chr_aaa")


def test_open_ended_years_overlap() -> None:
    assert years_overlap(184, None, 190, 200) is True
    assert years_overlap(201, 219, 184, 200) is False


async def _create_character(client: AsyncClient, project_id: str, payload: dict[str, object]) -> str:
    response = await client.post(f"/api/v1/projects/{project_id}/characters", json=payload)
    assert response.status_code == 201
    return str(response.json()["data"]["id"])


@pytest.mark.asyncio
async def test_sworn_relationship_is_visible_from_both_sides(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    liu_id = await _create_character(client, project_id, LIU_BEI)
    guan_id = await _create_character(client, project_id, GUAN_YU)
    created = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": liu_id,
            "to_character_id": guan_id,
            "relationship_type": "sworn",
            "intimacy": 95,
            "start_year": 184,
            "note": "桃园结义在史实中不可当作事实，这里只作游戏关系。",
        },
    )
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["id"].startswith("rel_")
    assert body["symmetric"] is True
    assert body["is_primary"] is True

    listing = await client.get(f"/api/v1/projects/{project_id}/relationships")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] == 1

    liu_graph = await client.get(f"/api/v1/projects/{project_id}/characters/{liu_id}/relationships")
    guan_graph = await client.get(f"/api/v1/projects/{project_id}/characters/{guan_id}/relationships")
    assert liu_graph.json()["data"]["edges"][0]["to_character"]["name"] == "关羽"
    assert liu_graph.json()["data"]["edges"][0]["direction"] == "outgoing"
    assert guan_graph.json()["data"]["edges"][0]["to_character"]["name"] == "刘备"
    assert guan_graph.json()["data"]["edges"][0]["intimacy"] == 95


@pytest.mark.asyncio
async def test_reject_self_and_overlapping_same_type(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    liu_id = await _create_character(client, project_id, LIU_BEI)
    guan_id = await _create_character(client, project_id, GUAN_YU)
    self_rel = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={"from_character_id": liu_id, "to_character_id": liu_id, "relationship_type": "kinship"},
    )
    assert self_rel.status_code == 400

    first = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": liu_id,
            "to_character_id": guan_id,
            "relationship_type": "sworn",
            "start_year": 184,
            "end_year": 200,
        },
    )
    assert first.status_code == 201
    duplicate = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": guan_id,
            "to_character_id": liu_id,
            "relationship_type": "sworn",
            "start_year": 190,
            "end_year": 210,
        },
    )
    assert duplicate.status_code == 409

    later = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": liu_id,
            "to_character_id": guan_id,
            "relationship_type": "sworn",
            "start_year": 201,
            "end_year": 219,
        },
    )
    assert later.status_code == 201


@pytest.mark.asyncio
async def test_asymmetric_ruler_subject_shows_incoming_on_subject(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    liu_id = await _create_character(client, project_id, LIU_BEI)
    zhuge_id = await _create_character(client, project_id, ZHUGE_LIANG)
    created = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": liu_id,
            "to_character_id": zhuge_id,
            "relationship_type": "ruler_subject",
            "start_year": 207,
            "note": "君臣：from 为君，to 为臣",
        },
    )
    assert created.status_code == 201
    assert created.json()["data"]["symmetric"] is False

    listing = await client.get(f"/api/v1/projects/{project_id}/relationships")
    assert listing.json()["meta"]["total"] == 1

    zhuge_graph = await client.get(f"/api/v1/projects/{project_id}/characters/{zhuge_id}/relationships")
    edges = zhuge_graph.json()["data"]["edges"]
    assert len(edges) == 1
    assert edges[0]["direction"] == "incoming"
    assert edges[0]["from_character"]["name"] == "刘备"


@pytest.mark.asyncio
async def test_update_and_delete_relationship_pair(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    liu_id = await _create_character(client, project_id, LIU_BEI)
    zhang_id = await _create_character(client, project_id, ZHANG_FEI)
    created = await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={
            "from_character_id": liu_id,
            "to_character_id": zhang_id,
            "relationship_type": "sworn",
            "intimacy": 80,
        },
    )
    rel_id = created.json()["data"]["id"]
    updated = await client.put(
        f"/api/v1/projects/{project_id}/relationships/{rel_id}",
        json={"relationship_type": "sworn", "intimacy": 99, "hostility": 0, "note": "更新后的结义"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["intimacy"] == 99

    zhang_graph = await client.get(f"/api/v1/projects/{project_id}/characters/{zhang_id}/relationships")
    assert zhang_graph.json()["data"]["edges"][0]["intimacy"] == 99

    deleted = await client.delete(f"/api/v1/projects/{project_id}/relationships/{rel_id}")
    assert deleted.status_code == 200
    empty = await client.get(f"/api/v1/projects/{project_id}/characters/{liu_id}/relationships")
    assert empty.json()["data"]["edges"] == []


@pytest.mark.asyncio
async def test_delete_character_cascades_relationships(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    liu_id = await _create_character(client, project_id, LIU_BEI)
    guan_id = await _create_character(client, project_id, GUAN_YU)
    await client.post(
        f"/api/v1/projects/{project_id}/relationships",
        json={"from_character_id": liu_id, "to_character_id": guan_id, "relationship_type": "sworn"},
    )
    deleted = await client.delete(f"/api/v1/projects/{project_id}/characters/{liu_id}")
    assert deleted.status_code == 200
    listing = await client.get(f"/api/v1/projects/{project_id}/relationships")
    assert listing.json()["data"] == []
    guan_graph = await client.get(f"/api/v1/projects/{project_id}/characters/{guan_id}/relationships")
    assert guan_graph.json()["data"]["edges"] == []
