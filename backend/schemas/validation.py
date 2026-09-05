"""校验报告 Schema。"""

from pydantic import BaseModel, Field

from backend.validation.types import IssueSeverity, ValidationMode


class ValidationIssueRead(BaseModel):
    """单条跨实体问题。"""

    rule: str
    severity: IssueSeverity
    message: str
    entity_type: str
    entity_id: str | None = None
    field: str | None = None


class ValidationReportRead(BaseModel):
    """项目校验报告。valid 只看 error，警告不阻断。"""

    mode: ValidationMode
    valid: bool
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    issues: list[ValidationIssueRead]
