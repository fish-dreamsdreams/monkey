"""从冻结导出目录加载游戏数据。

禁止写回编辑器工作库；本模块不 import backend。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from game_data_loader.contract import (
    assert_frozen_schema,
    package_files,
    verify_checksums,
)
from game_data_loader.errors import ClientPackageError
from game_data_loader.models import (
    GameData,
    RuntimeCharacter,
    RuntimeCity,
    RuntimeFaction,
    RuntimeSkill,
)


def load_export_dir(path: str | Path) -> GameData:
    """读取 exports/vN 目录：manifest + 分区 JSON。"""
    root = Path(path)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ClientPackageError(f"缺少 manifest.json: {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema_version = str(manifest.get("schema_version") or "")
    assert_frozen_schema(schema_version)
    sections: dict[str, object] = {}
    for name in package_files():
        file_path = root / name
        if not file_path.is_file():
            raise ClientPackageError(f"缺少分区文件: {name}")
        sections[name] = json.loads(file_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ClientPackageError("manifest.files 缺失")
    verify_checksums({str(key): str(value) for key, value in files.items()}, sections)
    return _to_game_data(manifest, sections)


def _to_game_data(manifest: dict[str, Any], sections: dict[str, object]) -> GameData:
    characters = tuple(_character(item) for item in _as_list(sections["characters.json"]))
    cities = tuple(_city(item) for item in _as_list(sections["cities.json"]))
    factions = tuple(_faction(item) for item in _as_list(sections["factions.json"]))
    skills = tuple(_skill(item) for item in _as_list(sections["skills.json"]))
    stories = tuple(str(item.get("code")) for item in _as_list(sections["stories.json"]) if item.get("code"))
    events = tuple(str(item.get("code")) for item in _as_list(sections["events.json"]) if item.get("code"))
    project = sections["project.json"]
    if not isinstance(project, dict):
        raise ClientPackageError("project.json 必须是对象")
    return GameData(
        schema_version=str(manifest["schema_version"]),
        content_version=int(manifest["content_version"]),
        project_code=str(manifest.get("project_code") or project.get("code") or ""),
        project_name=str(manifest.get("project_name") or project.get("name") or ""),
        characters=characters,
        cities=cities,
        factions=factions,
        skills=skills,
        story_codes=stories,
        event_codes=events,
    )


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ClientPackageError("分区应为数组")
    return [item for item in value if isinstance(item, dict)]


def _character(item: dict[str, Any]) -> RuntimeCharacter:
    base = item.get("base") if isinstance(item.get("base"), dict) else {}
    game = item.get("game") if isinstance(item.get("game"), dict) else {}
    return RuntimeCharacter(
        id=str(item.get("id") or ""),
        code=str(base.get("code") or item.get("code") or ""),
        name=str(base.get("name") or item.get("name") or ""),
        courtesy_name=base.get("courtesy_name"),
        birth_year=base.get("birth_year"),
        death_year=base.get("death_year"),
        force=int(game.get("force") or 0),
        intelligence=int(game.get("intelligence") or 0),
        politics=int(game.get("politics") or 0),
        charisma=int(game.get("charisma") or 0),
        leadership=int(game.get("leadership") or 0),
        stamina=int(game.get("stamina") or 0),
        morale=int(game.get("morale") or 0),
        mobility=int(game.get("mobility") or 0),
    )


def _city(item: dict[str, Any]) -> RuntimeCity:
    game = item.get("game") if isinstance(item.get("game"), dict) else {}
    return RuntimeCity(
        id=str(item.get("id") or ""),
        code=str(item.get("code") or ""),
        name=str(item.get("name") or ""),
        population=int(game.get("population") or 0),
        defense=int(game.get("defense") or 0),
    )


def _faction(item: dict[str, Any]) -> RuntimeFaction:
    meta = item.get("faction") if isinstance(item.get("faction"), dict) else item
    members = item.get("members") if isinstance(item.get("members"), list) else []
    member_ids: list[str] = []
    for member in members:
        if not isinstance(member, dict):
            continue
        character = member.get("character") if isinstance(member.get("character"), dict) else {}
        character_id = character.get("id") or member.get("character_id")
        if character_id:
            member_ids.append(str(character_id))
    return RuntimeFaction(
        id=str(meta.get("id") or ""),
        code=str(meta.get("code") or ""),
        name=str(meta.get("name") or ""),
        color=str(meta.get("color") or ""),
        member_character_ids=tuple(member_ids),
    )


def _skill(item: dict[str, Any]) -> RuntimeSkill:
    effects = item.get("effects") if isinstance(item.get("effects"), list) else []
    return RuntimeSkill(
        id=str(item.get("id") or ""),
        code=str(item.get("code") or ""),
        name=str(item.get("name") or ""),
        skill_type=str(item.get("skill_type") or ""),
        effects=tuple(effect for effect in effects if isinstance(effect, dict)),
    )
