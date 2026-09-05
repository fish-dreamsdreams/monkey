"""历史事件领域规则。

职责：校验事件日期，以及参与人物生卒、势力与城池存续。不执行任何游戏后果。
"""

from enum import Enum

from backend.core.exceptions import ValidationError
from backend.domain.year_range import contains_year

_DAYS_IN_MONTH = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class EventType(str, Enum):
    """事件类型。后果只作为文本记录。"""

    BATTLE = "battle"
    SIEGE = "siege"
    DIPLOMACY = "diplomacy"
    APPOINTMENT = "appointment"
    DEATH = "death"
    FOUNDING = "founding"
    CAPTURE = "capture"
    OTHER = "other"


EVENT_TYPE_LABELS_ZH: dict[EventType, str] = {
    EventType.BATTLE: "战役",
    EventType.SIEGE: "围城",
    EventType.DIPLOMACY: "外交",
    EventType.APPOINTMENT: "任命",
    EventType.DEATH: "卒殁",
    EventType.FOUNDING: "肇建",
    EventType.CAPTURE: "易主/攻占",
    EventType.OTHER: "其他",
}


class EventParticipantRole(str, Enum):
    """人物在事件中的角色。"""

    COMMANDER = "commander"
    PARTICIPANT = "participant"
    VICTIM = "victim"
    WITNESS = "witness"
    ENVOY = "envoy"


EVENT_PARTICIPANT_ROLE_LABELS_ZH: dict[EventParticipantRole, str] = {
    EventParticipantRole.COMMANDER: "主事/主将",
    EventParticipantRole.PARTICIPANT: "参与者",
    EventParticipantRole.VICTIM: "遇害/当事",
    EventParticipantRole.WITNESS: "在场",
    EventParticipantRole.ENVOY: "使节",
}


class EventFactionRole(str, Enum):
    """势力在事件中的角色。"""

    ATTACKER = "attacker"
    DEFENDER = "defender"
    HOST = "host"
    INVOLVED = "involved"


EVENT_FACTION_ROLE_LABELS_ZH: dict[EventFactionRole, str] = {
    EventFactionRole.ATTACKER: "攻方",
    EventFactionRole.DEFENDER: "守方",
    EventFactionRole.HOST: "主事方",
    EventFactionRole.INVOLVED: "相关",
}


def validate_event_date(year: int, month: int | None, day: int | None) -> None:
    """年必填；有日必须有月；日不能超过该月天数（二月允许 29）。"""
    if month is None and day is not None:
        raise ValidationError("填写日期时必须同时填写月份", field="month")
    if month is not None and (month < 1 or month > 12):
        raise ValidationError("月份必须介于 1 与 12 之间", field="month")
    if day is not None:
        assert month is not None
        if day < 1 or day > _DAYS_IN_MONTH[month]:
            raise ValidationError("日期超出该月天数", field="day")


def validate_character_alive_in_year(
    *,
    character_name: str,
    birth_year: int | None,
    death_year: int | None,
    event_year: int,
) -> None:
    """参与者必须落在生卒年之内。缺省生卒视为未知，不拦截。"""
    if birth_year is not None and event_year < birth_year:
        raise ValidationError(f"{character_name} 在 {event_year} 年尚未出生", field="character_id")
    if death_year is not None and event_year > death_year:
        raise ValidationError(f"{character_name} 在 {event_year} 年已经去世", field="character_id")


def validate_faction_exists_in_year(
    *,
    faction_name: str,
    start_year: int | None,
    end_year: int | None,
    event_year: int,
) -> None:
    """势力必须在事件年仍存续。"""
    if not contains_year(start_year, end_year, event_year):
        raise ValidationError(f"{faction_name} 在 {event_year} 年并不存在", field="faction_id")


def validate_city_exists_in_year(
    *,
    city_name: str,
    founded_year: int | None,
    destroyed_year: int | None,
    event_year: int,
) -> None:
    """事件地点必须落在城池存续年内。"""
    if not contains_year(founded_year, destroyed_year, event_year):
        raise ValidationError(f"{city_name} 在 {event_year} 年并不存在", field="location_city_id")
