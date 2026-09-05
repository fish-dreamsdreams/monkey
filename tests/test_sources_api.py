"""Phase 3 史料来源测试。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.source_types import BoundLayer, SourceType, validate_citation_layer, validate_source_definition

from tests.test_characters_api import LIU_BEI, _create_project


def test_romance_cannot_be_official_history() -> None:
    with pytest.raises(ValidationError):
        validate_source_definition("三国演义", SourceType.OFFICIAL_HISTORY)


def test_literary_cannot_bind_historical_layer() -> None:
    with pytest.raises(ValidationError):
        validate_citation_layer(SourceType.LITERARY, BoundLayer.HISTORICAL)


@pytest.mark.asyncio
async def test_project_seeds_official_history_and_romance(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.get(f"/api/v1/projects/{project_id}/sources")
    assert response.status_code == 200
    items = response.json()["data"]
    by_code = {item["code"]: item for item in items}
    assert by_code["sanguozhi"]["source_type"] == "official_history"
    assert by_code["sanguozhi"]["fact_eligible"] is True
    assert by_code["sanguoyanyi"]["source_type"] == "literary"
    assert by_code["sanguoyanyi"]["fact_eligible"] is False
    assert by_code["game_setting"]["source_type"] == "game_setting"


@pytest.mark.asyncio
async def test_character_can_cite_history_and_romance_separately(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    payload = {
        **LIU_BEI,
        "sources": [
            {
                "source_code": "sanguozhi",
                "bound_layer": "historical",
                "quotation": "先主姓刘，讳备，字玄德，涿郡涿县人。",
                "reference": "蜀书·先主传",
            },
            {
                "source_code": "sanguoyanyi",
                "bound_layer": "literary",
                "quotation": "桃园三结义。",
                "note": "文学情节，不得当作史实。",
            },
        ],
    }
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=payload)
    assert created.status_code == 201
    sources = created.json()["data"]["sources"]
    assert len(sources) == 2
    layers = {item["source_code"]: item["bound_layer"] for item in sources}
    assert layers["sanguozhi"] == "historical"
    assert layers["sanguoyanyi"] == "literary"
    assert created.json()["data"]["personalities"][0]["description"]


@pytest.mark.asyncio
async def test_reject_romance_as_historical_fact_source(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = created.json()["data"]["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/characters/{character_id}/sources",
        json={
            "source_code": "sanguoyanyi",
            "bound_layer": "historical",
            "quotation": "三英战吕布",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_reject_naming_romance_as_official_history(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.post(
        f"/api/v1/projects/{project_id}/sources",
        json={"code": "fake_yanyi", "name": "三国演义评注", "source_type": "official_history"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_and_delete_character_citation(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = created.json()["data"]["id"]
    added = await client.post(
        f"/api/v1/projects/{project_id}/characters/{character_id}/sources",
        json={
            "source_code": "sanguozhi",
            "bound_layer": "historical",
            "reference": "先主传",
        },
    )
    assert added.status_code == 201
    citation_id = added.json()["data"]["id"]
    assert citation_id.startswith("cit_")

    deleted = await client.delete(
        f"/api/v1/projects/{project_id}/characters/{character_id}/sources/{citation_id}"
    )
    assert deleted.status_code == 200
    detail = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert detail.json()["data"]["sources"] == []
