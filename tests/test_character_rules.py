"""人物领域规则测试。"""

import pytest

from backend.core.exceptions import ValidationError
from backend.domain.character_rules import validate_historical_year_range, validate_lifespan


def test_lifespan_accepts_valid_years() -> None:
    validate_lifespan(161, 223)
    validate_lifespan(161, None)
    validate_lifespan(None, 223)
    validate_lifespan(None, None)


def test_lifespan_rejects_birth_after_death() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_lifespan(223, 161)
    assert exc.value.field == "death_year"


def test_project_year_range_rejects_inverted_span() -> None:
    with pytest.raises(ValidationError):
        validate_historical_year_range(220, 184)
