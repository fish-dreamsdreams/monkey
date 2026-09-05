"""技能 Schema。效果字段只接受数据，不接受脚本。"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.core.exceptions import ValidationError as DomainValidationError
from backend.domain.skill_rules import (
    COST_RESOURCES,
    SkillEffectType,
    SkillTarget,
    SkillType,
    validate_effect_payload,
    validate_skill_type_constraints,
    validate_trigger_event,
)
from backend.domain.source_types import SourceType


class SkillCost(BaseModel):
    """技能消耗。客户端扣值，编辑器只存参数。"""

    resource: str = "none"
    amount: int = Field(default=0, ge=0, le=100)

    @field_validator("resource")
    @classmethod
    def normalize_resource(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in COST_RESOURCES:
            raise ValueError("消耗资源只能是 none、stamina 或 morale")
        return normalized


class SkillTrigger(BaseModel):
    """触发条件数据。"""

    event: str = Field(min_length=1, max_length=64)
    threshold: int | None = Field(default=None, ge=0, le=100)


class SkillEffect(BaseModel):
    """单条效果 payload。"""

    type: SkillEffectType
    target: SkillTarget = SkillTarget.SELF
    stat: str | None = None
    delta: int | None = Field(default=None, ge=-100, le=100)
    amount: int | None = Field(default=None, ge=0, le=10000)
    status_code: str | None = Field(default=None, max_length=64)
    duration: int | None = Field(default=None, ge=0, le=99)
    params: dict[str, int | str | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> SkillEffect:
        try:
            validate_effect_payload(
                effect_type=self.type,
                stat=self.stat,
                delta=self.delta,
                amount=self.amount,
                status_code=self.status_code,
                params=dict(self.params),
            )
        except DomainValidationError as exc:
            raise ValueError(exc.message) from exc
        return self


class SkillHistoricalBasis(BaseModel):
    """技能史源。演义技能应标 literary，不得据此改写人物史实栏。"""

    source_type: SourceType | None = None
    source_code: str | None = Field(default=None, max_length=64)
    note: str | None = None


class SkillWrite(BaseModel):
    """创建或更新技能。"""

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    skill_type: SkillType
    description: str | None = None
    target: SkillTarget = SkillTarget.SELF
    cooldown: int = Field(default=0, ge=0, le=99)
    cost: SkillCost = Field(default_factory=SkillCost)
    trigger_condition: SkillTrigger | None = None
    effects: list[SkillEffect] = Field(min_length=1)
    historical_basis: SkillHistoricalBasis | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_definition(self) -> SkillWrite:
        try:
            validate_skill_type_constraints(self.skill_type, self.cooldown, self.cost.amount)
            if self.trigger_condition is not None:
                validate_trigger_event(self.trigger_condition.event)
        except DomainValidationError as exc:
            raise ValueError(exc.message) from exc
        return self


class SkillRead(BaseModel):
    """技能定义。"""

    id: str
    project_id: str
    code: str
    name: str
    skill_type: SkillType
    description: str | None
    target: SkillTarget
    cooldown: int
    cost: SkillCost
    trigger_condition: SkillTrigger | None
    effects: list[SkillEffect]
    historical_basis: SkillHistoricalBasis | None


class CharacterSkillWrite(BaseModel):
    """把技能绑到人物上。"""

    skill_id: str = Field(min_length=36, max_length=36)
    level: int = Field(default=1, ge=1, le=10)
    source_note: str | None = None


class CharacterSkillUpdate(BaseModel):
    """更新人物技能等级或来源说明。"""

    level: int = Field(ge=1, le=10)
    source_note: str | None = None


class CharacterSkillRead(BaseModel):
    """人物技能绑定。"""

    id: str
    character_id: str
    skill: SkillRead
    level: int
    source_note: str | None


class SkillTypeMeta(BaseModel):
    """技能或效果类型说明。"""

    code: str
    name_zh: str
