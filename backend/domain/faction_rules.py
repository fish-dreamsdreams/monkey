"""城池与势力领域规则。

职责：校验时序归属，禁止同一时段一城两属、一人两势。势力由用户创建，不内置魏蜀吴。
"""

from enum import Enum

from backend.core.exceptions import ConflictError, ValidationError
from backend.domain.year_range import validate_year_range, years_overlap


class FactionMemberRole(str, Enum):
    """势力成员角色。领袖以成员记录为准，势力表上的 leader 仅为快捷指针。"""

    LEADER = "leader"
    HEIR = "heir"
    OFFICER = "officer"
    MEMBER = "member"


FACTION_MEMBER_ROLE_LABELS_ZH: dict[FactionMemberRole, str] = {
    FactionMemberRole.LEADER: "领袖",
    FactionMemberRole.HEIR: "继承人",
    FactionMemberRole.OFFICER: "属官",
    FactionMemberRole.MEMBER: "成员",
}


def validate_city_years(founded_year: int | None, destroyed_year: int | None) -> None:
    """建城年不能晚于毁城年。"""
    validate_year_range(
        founded_year,
        destroyed_year,
        field="destroyed_year",
        message="建城年份不能晚于毁城年份",
    )


def validate_interval_within(
    *,
    inner_start: int | None,
    inner_end: int | None,
    outer_start: int | None,
    outer_end: int | None,
    field: str,
    message: str,
) -> None:
    """内层时段不能落到外层时段之外。外层空值表示不限制。"""
    if outer_start is not None and inner_end is not None and inner_end < outer_start:
        raise ValidationError(message, field=field)
    if outer_end is not None and inner_start is not None and inner_start > outer_end:
        raise ValidationError(message, field=field)
    if outer_start is not None and inner_start is not None and inner_start < outer_start:
        raise ValidationError(message, field=field)
    if outer_end is not None and inner_end is not None and inner_end > outer_end:
        raise ValidationError(message, field=field)


def assert_no_overlap(
    existing: list[tuple[int | None, int | None]],
    start_year: int | None,
    end_year: int | None,
    message: str,
) -> None:
    """已有时段与新时段不能重叠。"""
    for left_start, left_end in existing:
        if years_overlap(left_start, left_end, start_year, end_year):
            raise ConflictError(message)
