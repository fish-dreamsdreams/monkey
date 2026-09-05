"""年代区间工具。

职责：统一处理可空起止年的包含与重叠判断，供关系、势力成员、领土复用。
"""

from backend.core.exceptions import ValidationError

_UNBOUNDED = 10**9


def validate_year_range(
    start_year: int | None,
    end_year: int | None,
    *,
    field: str = "end_year",
    message: str = "起始年份不能晚于结束年份",
) -> None:
    """起始年不能晚于结束年。"""
    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValidationError(message, field=field)


def years_overlap(
    left_start: int | None,
    left_end: int | None,
    right_start: int | None,
    right_end: int | None,
) -> bool:
    """空年份视为不设限。"""
    left_from = left_start if left_start is not None else -_UNBOUNDED
    left_to = left_end if left_end is not None else _UNBOUNDED
    right_from = right_start if right_start is not None else -_UNBOUNDED
    right_to = right_end if right_end is not None else _UNBOUNDED
    return left_from <= right_to and right_from <= left_to


def contains_year(start_year: int | None, end_year: int | None, year: int) -> bool:
    """判断某年是否落在区间内。"""
    return years_overlap(start_year, end_year, year, year)
