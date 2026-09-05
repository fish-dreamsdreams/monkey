"""人物关系类型与校验。

职责：定义关系种类、对称/不对称语义，以及时段重叠、自指等编辑期规则。
血缘在本阶段表示“存在血缘联系”，不细分父子角色。
"""

from enum import Enum

from backend.core.exceptions import ValidationError


class RelationshipType(str, Enum):
    """关系类型。"""

    KINSHIP = "kinship"
    MARRIAGE = "marriage"
    SWORN = "sworn"
    RULER_SUBJECT = "ruler_subject"
    MASTER_SERVANT = "master_servant"
    MENTOR_STUDENT = "mentor_student"
    RIVAL = "rival"
    ALLIANCE = "alliance"


RELATIONSHIP_TYPE_LABELS_ZH: dict[RelationshipType, str] = {
    RelationshipType.KINSHIP: "血缘",
    RelationshipType.MARRIAGE: "婚姻",
    RelationshipType.SWORN: "结义",
    RelationshipType.RULER_SUBJECT: "君臣",
    RelationshipType.MASTER_SERVANT: "主从",
    RelationshipType.MENTOR_STUDENT: "师徒",
    RelationshipType.RIVAL: "仇敌",
    RelationshipType.ALLIANCE: "同盟",
}

SYMMETRIC_RELATIONSHIP_TYPES: frozenset[RelationshipType] = frozenset(
    {
        RelationshipType.KINSHIP,
        RelationshipType.MARRIAGE,
        RelationshipType.SWORN,
        RelationshipType.RIVAL,
        RelationshipType.ALLIANCE,
    }
)

_UNBOUNDED = 10**9


def is_symmetric(relationship_type: RelationshipType) -> bool:
    """对称关系会同时写入反向边，保证双方视角一致。"""
    return relationship_type in SYMMETRIC_RELATIONSHIP_TYPES


def validate_not_self(from_character_id: str, to_character_id: str) -> None:
    """禁止人物与自己建立关系。"""
    if from_character_id == to_character_id:
        raise ValidationError("人物不能与自己建立关系", field="to_character_id")


def validate_relationship_years(start_year: int | None, end_year: int | None) -> None:
    """关系起始年不能晚于结束年。"""
    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValidationError("关系起始年份不能晚于结束年份", field="end_year")


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


def validate_years_against_lifespan(
    *,
    from_birth: int | None,
    from_death: int | None,
    to_birth: int | None,
    to_death: int | None,
    start_year: int | None,
    end_year: int | None,
) -> None:
    """关系不能完全落在双方都已去世之后。"""
    deaths = [year for year in (from_death, to_death) if year is not None]
    if start_year is not None and deaths and start_year > max(deaths):
        raise ValidationError("关系起始年不能晚于双方卒年", field="start_year")
    births = [year for year in (from_birth, to_birth) if year is not None]
    if end_year is not None and births and end_year < min(births):
        raise ValidationError("关系结束年不能早于双方生年", field="end_year")
