"""校验报告类型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationMode(str, Enum):
    """校验模式。strict 按史实拦截；narrative 允许已标注来源的传说例外。"""

    STRICT_HISTORICAL = "strict_historical"
    GAME_NARRATIVE = "game_narrative"


VALIDATION_MODE_LABELS_ZH: dict[ValidationMode, str] = {
    ValidationMode.STRICT_HISTORICAL: "严格史实",
    ValidationMode.GAME_NARRATIVE: "游戏叙事",
}


class IssueSeverity(str, Enum):
    """问题级别。只有 error 会使 valid=false。"""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationIssue:
    """一条跨实体问题。"""

    rule: str
    severity: IssueSeverity
    message: str
    entity_type: str
    entity_id: str | None = None
    field: str | None = None


@dataclass
class ValidationReport:
    """项目级校验报告。"""

    mode: ValidationMode
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [item for item in self.issues if item.severity == IssueSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [item for item in self.issues if item.severity == IssueSeverity.WARNING]

    @property
    def valid(self) -> bool:
        return not self.errors
