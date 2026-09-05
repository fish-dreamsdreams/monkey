"""人物领域规则。

职责：校验历史身份层的时间合法性，不处理游戏数值平衡。
"""

from backend.core.exceptions import ValidationError


def validate_lifespan(birth_year: int | None, death_year: int | None) -> None:
    """校验生卒年：出生年份不能晚于死亡年份。"""
    if birth_year is not None and death_year is not None and birth_year > death_year:
        raise ValidationError("人物出生年份不能晚于死亡年份", field="death_year")


def validate_historical_year_range(start_year: int | None, end_year: int | None) -> None:
    """校验项目目标年代范围。"""
    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValidationError("项目起始年份不能晚于结束年份", field="target_end_year")
