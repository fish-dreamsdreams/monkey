"""Phase 5 技能系统测试。效果只作为数据，不结算战斗。"""

import pytest
from httpx import AsyncClient

from backend.core.exceptions import ValidationError
from backend.domain.skill_rules import SkillEffectType, validate_effect_payload, validate_skill_type_constraints
from backend.domain.skill_rules import SkillType

from tests.test_characters_api import LIU_BEI, _create_project

EMPTY_FORT = {
    "code": "skl_empty_fort",
    "name": "空城计",
    "skill_type": "command",
    "description": "演义计策，客户端解释效果；编辑器不结算。",
    "target": "enemy",
    "cooldown": 5,
    "cost": {"resource": "morale", "amount": 10},
    "trigger_condition": {"event": "on_defend"},
    "effects": [
        {
            "type": "apply_status",
            "target": "enemy",
            "status_code": "hesitate",
            "duration": 1,
        }
    ],
    "historical_basis": {
        "source_type": "literary",
        "source_code": "sanguoyanyi",
        "note": "出自三国演义，不得写入人物史实栏。",
    },
}


def test_passive_skill_cannot_have_cooldown() -> None:
    with pytest.raises(ValidationError):
        validate_skill_type_constraints(SkillType.PASSIVE, cooldown=3, cost_amount=0)


def test_effect_rejects_script_params() -> None:
    with pytest.raises(ValidationError):
        validate_effect_payload(
            effect_type=SkillEffectType.MODIFY_STAT,
            stat="mobility",
            delta=-20,
            amount=None,
            status_code=None,
            params={"eval": "damage()"},
        )


async def _create_character(client: AsyncClient, project_id: str) -> str:
    response = await client.post(f"/api/v1/projects/{project_id}/characters", json=LIU_BEI)
    assert response.status_code == 201
    return str(response.json()["data"]["id"])


@pytest.mark.asyncio
async def test_create_literary_skill_and_bind_to_character(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/api/v1/projects/{project_id}/skills", json=EMPTY_FORT)
    assert created.status_code == 201
    skill = created.json()["data"]
    assert skill["id"].startswith("skl_")
    assert skill["effects"][0]["type"] == "apply_status"
    assert skill["historical_basis"]["source_type"] == "literary"

    character_id = await _create_character(client, project_id)
    bound = await client.post(
        f"/api/v1/projects/{project_id}/characters/{character_id}/skills",
        json={"skill_id": skill["id"], "level": 3, "source_note": "游戏设定，非正史记载。"},
    )
    assert bound.status_code == 201
    assert bound.json()["data"]["id"].startswith("csk_")
    assert bound.json()["data"]["level"] == 3

    detail = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}")
    assert "空城计" not in (detail.json()["data"]["historical"]["biography"] or "")

    listing = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}/skills")
    assert listing.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_reject_invalid_effect_and_script_type(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    missing_stat = await client.post(
        f"/api/v1/projects/{project_id}/skills",
        json={
            "code": "skl_bad_stat",
            "name": "错误效果",
            "skill_type": "active",
            "effects": [{"type": "modify_stat", "target": "enemy"}],
        },
    )
    assert missing_stat.status_code == 422

    script = await client.post(
        f"/api/v1/projects/{project_id}/skills",
        json={
            "code": "skl_script",
            "name": "脚本攻击",
            "skill_type": "active",
            "effects": [{"type": "eval_script", "params": {"code": "hit()"}}],
        },
    )
    assert script.status_code == 422

    passive_cd = await client.post(
        f"/api/v1/projects/{project_id}/skills",
        json={
            "code": "skl_passive_cd",
            "name": "错误被动",
            "skill_type": "passive",
            "cooldown": 2,
            "effects": [{"type": "modify_stat", "stat": "force", "delta": 5, "target": "self"}],
        },
    )
    assert passive_cd.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_bind_and_delete_skill_unbinds(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    skill = await client.post(
        f"/api/v1/projects/{project_id}/skills",
        json={
            "code": "skl_charge",
            "name": "突击",
            "skill_type": "active",
            "cooldown": 1,
            "effects": [{"type": "deal_damage", "target": "enemy", "amount": 20}],
        },
    )
    skill_id = skill.json()["data"]["id"]
    character_id = await _create_character(client, project_id)
    first = await client.post(
        f"/api/v1/projects/{project_id}/characters/{character_id}/skills",
        json={"skill_id": skill_id, "level": 1},
    )
    assert first.status_code == 201
    duplicate = await client.post(
        f"/api/v1/projects/{project_id}/characters/{character_id}/skills",
        json={"skill_id": skill_id, "level": 2},
    )
    assert duplicate.status_code == 409

    binding_id = first.json()["data"]["id"]
    updated = await client.put(
        f"/api/v1/projects/{project_id}/characters/{character_id}/skills/{binding_id}",
        json={"level": 8, "source_note": "数值可调"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["level"] == 8

    deleted = await client.delete(f"/api/v1/projects/{project_id}/skills/{skill_id}")
    assert deleted.status_code == 200
    remaining = await client.get(f"/api/v1/projects/{project_id}/characters/{character_id}/skills")
    assert remaining.json()["data"] == []
