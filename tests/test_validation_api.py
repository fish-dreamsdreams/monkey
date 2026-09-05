"""Phase 11 跨实体校验。时间线、易主重叠、剧情死循环。"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from httpx import AsyncClient

from backend.core.paths import project_assets_dir
from backend.domain.story_rules import GraphEdge, GraphNode
from backend.validation.engine import validate_project
from backend.validation.snapshots import (
    CharacterSnap,
    CitySnap,
    EventParticipantSnap,
    EventSnap,
    FactionSnap,
    ProjectSnapshot,
    StorySnap,
    TerritorySnap,
)
from backend.validation.types import IssueSeverity, ValidationMode
from tests.test_characters_api import LIU_BEI, _create_project


def test_dead_participant_is_error_in_strict_and_warning_in_narrative() -> None:
    snapshot = ProjectSnapshot(
        characters=[CharacterSnap("chr_a", "关羽", 160, 220)],
        events=[
            EventSnap(
                id="evt_a",
                name="荆州传说",
                year=230,
                layer="literary",
                location_city_id=None,
                participants=(
                    EventParticipantSnap("chr_a", "关羽", 160, 220),
                ),
                factions=(),
                source_types=("literary",),
            )
        ],
    )
    strict = validate_project(snapshot, ValidationMode.STRICT_HISTORICAL)
    assert strict.valid is False
    assert any(item.rule == "event_participant_alive" for item in strict.errors)

    narrative = validate_project(snapshot, ValidationMode.GAME_NARRATIVE)
    assert narrative.valid is True
    assert any(
        item.rule == "event_participant_alive" and item.severity == IssueSeverity.WARNING
        for item in narrative.warnings
    )


def test_city_ownership_overlap_is_reported() -> None:
    snapshot = ProjectSnapshot(
        cities=[CitySnap("cty_a", "成都", -311, None)],
        factions=[
            FactionSnap("fac_a", "左将军领", 184, 221),
            FactionSnap("fac_b", "汉中王", 219, 223),
        ],
        territories=[
            TerritorySnap("ftr_a", "cty_a", "成都", "fac_a", "左将军领", 214, 221),
            TerritorySnap("ftr_b", "cty_a", "成都", "fac_b", "汉中王", 219, 223),
        ],
    )
    report = validate_project(snapshot, ValidationMode.STRICT_HISTORICAL)
    assert report.valid is False
    assert any(item.rule == "city_ownership" for item in report.errors)


def test_unconditional_story_cycle_is_dead_loop() -> None:
    snapshot = ProjectSnapshot(
        stories=[
            StorySnap(
                id="sty_a",
                name="死循环",
                nodes=(
                    GraphNode("a", True, False),
                    GraphNode("b", False, True),
                ),
                edges=(
                    GraphEdge("a", "b", False, False),
                    GraphEdge("b", "a", False, False),
                ),
            )
        ]
    )
    report = validate_project(snapshot, ValidationMode.STRICT_HISTORICAL)
    assert report.valid is False
    assert any(item.rule == "story_cycle" for item in report.errors)


def test_narrative_legend_without_source_is_still_error() -> None:
    snapshot = ProjectSnapshot(
        events=[
            EventSnap(
                id="evt_b",
                name="无来源传说",
                year=230,
                layer="literary",
                location_city_id=None,
                participants=(EventParticipantSnap("chr_a", "关羽", 160, 220),),
                factions=(),
                source_types=(),
            )
        ]
    )
    report = validate_project(snapshot, ValidationMode.GAME_NARRATIVE)
    assert report.valid is False
    assert any(item.rule == "event_legend_source" for item in report.errors)


@pytest.mark.asyncio
async def test_empty_project_is_valid(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.get(f"/api/v1/projects/{project_id}/validation")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["valid"] is True
    assert body["mode"] == "strict_historical"
    assert body["issues"] == []


@pytest.mark.asyncio
async def test_incomplete_story_and_missing_file_fail_validation(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    story = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "draft", "name": "草稿", "layer": "game"},
    )
    story_id = story.json()["data"]["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "intro", "name": "开场", "node_type": "dialogue", "is_entry": True},
    )
    created = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "code": "res_tmp",
            "name": "临时头像",
            "resource_type": "portrait",
            "path": "portraits/tmp.png",
            "content_base64": base64.b64encode(b"tmp").decode("ascii"),
        },
    )
    assert created.status_code == 201
    Path(project_assets_dir(project_id) / "portraits" / "tmp.png").unlink()

    response = await client.get(f"/api/v1/projects/{project_id}/validation")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["valid"] is False
    rules = {item["rule"] for item in body["issues"]}
    assert "story_graph" in rules
    assert "resource_path" in rules
