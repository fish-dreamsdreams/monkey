"""客户端运行时只读对象。数值仅为数据，不在此结算战斗。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeCharacter:
    """人物运行时快照。historical 与 game 分栏已在包内拆开。"""

    id: str
    code: str
    name: str
    courtesy_name: str | None
    birth_year: int | None
    death_year: int | None
    force: int
    intelligence: int
    politics: int
    charisma: int
    leadership: int
    stamina: int
    morale: int
    mobility: int


@dataclass(frozen=True)
class RuntimeCity:
    """城池运行时快照。归属由势力领土按时段派生，不写死在城池上。"""

    id: str
    code: str
    name: str
    population: int
    defense: int


@dataclass(frozen=True)
class RuntimeFaction:
    """势力运行时快照。"""

    id: str
    code: str
    name: str
    color: str
    member_character_ids: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeSkill:
    """技能定义。effects 原样保留，由未来客户端解释。"""

    id: str
    code: str
    name: str
    skill_type: str
    effects: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class GameData:
    """一次导出包加载后的只读世界数据。"""

    schema_version: str
    content_version: int
    project_code: str
    project_name: str
    characters: tuple[RuntimeCharacter, ...]
    cities: tuple[RuntimeCity, ...]
    factions: tuple[RuntimeFaction, ...]
    skills: tuple[RuntimeSkill, ...]
    story_codes: tuple[str, ...]
    event_codes: tuple[str, ...]

    def character_by_code(self, code: str) -> RuntimeCharacter:
        """按业务 code 取人物。"""
        for item in self.characters:
            if item.code == code:
                return item
        raise KeyError(f"人物不存在: {code}")
