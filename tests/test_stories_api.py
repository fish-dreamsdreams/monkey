"""Phase 9 剧情节点图测试。无条件边禁止成环。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.story_rules import GraphEdge, GraphNode, analyze_story_graph, assert_edge_allowed
from tests.test_characters_api import LIU_BEI, _create_project


def test_unconditional_cycle_is_rejected() -> None:
    nodes = {"a", "b"}
    existing = [GraphEdge("a", "b", False, False)]
    with pytest.raises(ValidationError):
        assert_edge_allowed(nodes, existing, GraphEdge("b", "a", False, False))


def test_conditional_back_edge_needs_terminator() -> None:
    nodes = {"a", "b"}
    existing = [GraphEdge("a", "b", False, False)]
    with pytest.raises(ValidationError):
        assert_edge_allowed(nodes, existing, GraphEdge("b", "a", True, False))
    assert_edge_allowed(nodes, existing, GraphEdge("b", "a", True, True))


def test_entry_must_reach_ending() -> None:
    report = analyze_story_graph(
        [GraphNode("a", True, False), GraphNode("b", False, True)],
        [],
    )
    assert report.valid is False
    assert report.entry_reaches_ending is False


@pytest.mark.asyncio
async def test_create_linear_story_with_choice(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    character = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    character_id = character.json()["data"]["id"]

    created = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={
            "code": "peach_garden",
            "name": "桃园结义",
            "layer": "literary",
            "description": "演义叙事，不写入人物史实栏。",
        },
    )
    assert created.status_code == 201
    story = created.json()["data"]
    assert story["id"].startswith("sty_")
    assert story["graph"]["valid"] is False
    story_id = story["id"]

    chapter = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/chapters",
        json={"code": "ch1", "name": "结义", "sort_order": 1},
    )
    assert chapter.status_code == 201
    chapter_id = chapter.json()["data"]["id"]
    assert chapter_id.startswith("chp_")

    entry = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={
            "code": "intro",
            "name": "开场",
            "node_type": "dialogue",
            "chapter_id": chapter_id,
            "is_entry": True,
            "body": "刘关张相遇。",
        },
    )
    choice = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "swear", "name": "是否结义", "node_type": "choice"},
    )
    ending = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={
            "code": "oath",
            "name": "结义成功",
            "node_type": "reward",
            "is_ending": True,
            "body": "桃园结义（演义）。",
        },
    )
    assert entry.status_code == 201
    entry_id = entry.json()["data"]["id"]
    choice_id = choice.json()["data"]["id"]
    ending_id = ending.json()["data"]["id"]
    assert entry_id.startswith("snd_")

    linked = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{entry_id}/edges",
        json={"to_node_id": choice_id},
    )
    assert linked.status_code == 201
    assert linked.json()["data"]["id"].startswith("sed_")

    branch = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{choice_id}/choices",
        json={"label": "结为兄弟", "to_node_id": ending_id},
    )
    assert branch.status_code == 201
    assert branch.json()["data"]["id"].startswith("cho_")

    cast = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{entry_id}/characters",
        json={"character_id": character_id, "role": "speaker"},
    )
    assert cast.status_code == 201
    assert cast.json()["data"]["id"].startswith("snc_")

    detail = await client.get(f"/api/v1/projects/{project_id}/stories/{story_id}")
    graph = detail.json()["data"]["graph"]
    assert graph["valid"] is True
    assert graph["entry_reaches_ending"] is True
    assert graph["has_unconditional_cycle"] is False

    bio = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert "桃园" not in (bio.json()["data"]["historical"]["biography"] or "")


@pytest.mark.asyncio
async def test_reject_unconditional_cycle_and_allow_conditional_back_edge(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "loop_check", "name": "环检测", "layer": "game"},
    )
    story_id = created.json()["data"]["id"]
    start = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "start", "name": "入口", "node_type": "dialogue", "is_entry": True},
    )
    mid = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "mid", "name": "中段", "node_type": "condition"},
    )
    ending = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "end", "name": "结束", "node_type": "reward", "is_ending": True},
    )
    start_id = start.json()["data"]["id"]
    mid_id = mid.json()["data"]["id"]
    end_id = ending.json()["data"]["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{start_id}/edges",
        json={"to_node_id": mid_id},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{mid_id}/edges",
        json={"to_node_id": end_id},
    )
    cycle = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{end_id}/edges",
        json={"to_node_id": start_id},
    )
    assert cycle.status_code == 400

    missing_note = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{end_id}/edges",
        json={"to_node_id": start_id, "is_conditional": True},
    )
    assert missing_note.status_code == 400

    back = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes/{end_id}/edges",
        json={
            "to_node_id": start_id,
            "is_conditional": True,
            "condition_note": "未完成目标时可重试一次",
        },
    )
    assert back.status_code == 201
    detail = await client.get(f"/api/v1/projects/{project_id}/stories/{story_id}")
    assert detail.json()["data"]["graph"]["valid"] is True
    assert detail.json()["data"]["graph"]["has_unconditional_cycle"] is False


@pytest.mark.asyncio
async def test_historical_event_node_requires_existing_event(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    story = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "cite_event", "name": "引用事件", "layer": "literary"},
    )
    story_id = story.json()["data"]["id"]
    missing = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={"code": "need_event", "name": "缺事件", "node_type": "historical_event"},
    )
    assert missing.status_code == 400

    event = await client.post(
        f"/api/v1/projects/{project_id}/events",
        json={"code": "battle_red_cliffs", "name": "赤壁之战", "year": 208, "event_type": "battle"},
    )
    event_id = event.json()["data"]["id"]
    node = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/nodes",
        json={
            "code": "red_cliffs_scene",
            "name": "赤壁演出",
            "node_type": "historical_event",
            "event_id": event_id,
            "is_entry": True,
            "is_ending": True,
        },
    )
    assert node.status_code == 201
    assert node.json()["data"]["event"]["name"] == "赤壁之战"


@pytest.mark.asyncio
async def test_update_story_chapter(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    story = await client.post(
        f"/api/v1/projects/{project_id}/stories",
        json={"code": "peach_garden", "name": "桃园结义", "layer": "literary"},
    )
    story_id = story.json()["data"]["id"]
    chapter = await client.post(
        f"/api/v1/projects/{project_id}/stories/{story_id}/chapters",
        json={"code": "ch1", "name": "结义", "sort_order": 1},
    )
    chapter_id = chapter.json()["data"]["id"]
    updated = await client.put(
        f"/api/v1/projects/{project_id}/stories/{story_id}/chapters/{chapter_id}",
        json={"code": "ch1", "name": "桃园", "sort_order": 2, "summary": "结义开篇"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "桃园"
    assert updated.json()["data"]["sort_order"] == 2
    assert updated.json()["data"]["summary"] == "结义开篇"
