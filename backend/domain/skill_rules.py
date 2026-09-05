"""技能领域规则。

职责：校验技能类型约束与效果数据形状。只描述客户端可解释的 payload，不计算伤害、不执行脚本。
"""

from enum import Enum

from backend.core.exceptions import ValidationError


class SkillType(str, Enum):
    """技能分类。"""

    ACTIVE = "active"
    PASSIVE = "passive"
    COMMAND = "command"
    DOMESTIC = "domestic"


class SkillTarget(str, Enum):
    """效果作用对象。由客户端解释，编辑器不结算。"""

    SELF = "self"
    ALLY = "ally"
    ENEMY = "enemy"
    ALL_ALLIES = "all_allies"
    ALL_ENEMIES = "all_enemies"
    TILE = "tile"
    NONE = "none"


class SkillEffectType(str, Enum):
    """效果类型。禁止出现脚本/求值类类型。"""

    MODIFY_STAT = "modify_stat"
    DEAL_DAMAGE = "deal_damage"
    HEAL = "heal"
    APPLY_STATUS = "apply_status"
    MOVE = "move"
    REVEAL = "reveal"
    GAIN_RESOURCE = "gain_resource"


SKILL_TYPE_LABELS_ZH: dict[SkillType, str] = {
    SkillType.ACTIVE: "主动技能",
    SkillType.PASSIVE: "被动技能",
    SkillType.COMMAND: "统率技能",
    SkillType.DOMESTIC: "内政技能",
}

EFFECT_TYPE_LABELS_ZH: dict[SkillEffectType, str] = {
    SkillEffectType.MODIFY_STAT: "修改属性",
    SkillEffectType.DEAL_DAMAGE: "造成伤害（仅参数）",
    SkillEffectType.HEAL: "治疗（仅参数）",
    SkillEffectType.APPLY_STATUS: "施加状态",
    SkillEffectType.MOVE: "位移",
    SkillEffectType.REVEAL: "显隐/侦察",
    SkillEffectType.GAIN_RESOURCE: "获得资源",
}

ALLOWED_STATS: frozenset[str] = frozenset(
    {"force", "intelligence", "politics", "charisma", "leadership", "stamina", "morale", "mobility"}
)
ALLOWED_TRIGGER_EVENTS: frozenset[str] = frozenset(
    {"always", "battle_start", "turn_start", "hp_below", "on_attack", "on_defend"}
)
FORBIDDEN_PARAM_KEYS: frozenset[str] = frozenset({"eval", "exec", "python", "script", "bytecode", "code"})
COST_RESOURCES: frozenset[str] = frozenset({"none", "stamina", "morale"})


def validate_skill_type_constraints(skill_type: SkillType, cooldown: int, cost_amount: int) -> None:
    """被动技能不能带冷却或消耗。"""
    if skill_type == SkillType.PASSIVE and cooldown:
        raise ValidationError("被动技能冷却必须为 0", field="cooldown")
    if skill_type == SkillType.PASSIVE and cost_amount:
        raise ValidationError("被动技能不能设置消耗", field="cost")


def validate_trigger_event(event: str | None) -> None:
    """触发条件只允许预置事件名。"""
    if event is not None and event not in ALLOWED_TRIGGER_EVENTS:
        raise ValidationError(f"不支持的触发事件: {event}", field="trigger_condition")


def validate_effect_payload(
    *,
    effect_type: SkillEffectType,
    stat: str | None,
    delta: int | None,
    amount: int | None,
    status_code: str | None,
    params: dict[str, object],
) -> None:
    """校验单条效果数据。不执行任何战斗公式。"""
    forbidden = FORBIDDEN_PARAM_KEYS.intersection(params)
    if forbidden:
        raise ValidationError("技能效果只允许数据参数，禁止脚本字段", field="effects")
    if effect_type == SkillEffectType.MODIFY_STAT:
        if stat not in ALLOWED_STATS:
            raise ValidationError("modify_stat 必须指定合法属性名", field="effects")
        if delta is None:
            raise ValidationError("modify_stat 必须提供 delta", field="effects")
    if effect_type in {SkillEffectType.DEAL_DAMAGE, SkillEffectType.HEAL, SkillEffectType.GAIN_RESOURCE}:
        if amount is None:
            raise ValidationError(f"{effect_type.value} 必须提供 amount", field="effects")
    if effect_type == SkillEffectType.APPLY_STATUS and not status_code:
        raise ValidationError("apply_status 必须提供 status_code", field="effects")
