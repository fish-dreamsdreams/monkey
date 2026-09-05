"""导入导出领域规则测试。"""

import pytest

from backend.core.exceptions import UnsupportedSchemaError, ValidationError
from backend.core.schema_version import CURRENT_SCHEMA_VERSION
from backend.domain.export_rules import (
    PACKAGE_SECTION_FILES,
    assert_importable_schema,
    checksum_payload,
    parse_schema_version,
    verify_checksums,
)


def test_checksum_is_stable() -> None:
    first = checksum_payload({"name": "刘备", "items": [1, 2]})
    second = checksum_payload({"items": [1, 2], "name": "刘备"})
    assert first == second
    assert len(first) == 64


def test_parse_and_accept_current_schema() -> None:
    assert parse_schema_version("1.11.0") == (1, 11, 0)
    assert_importable_schema(CURRENT_SCHEMA_VERSION)
    assert_importable_schema("1.10.0")


def test_reject_unknown_schema() -> None:
    with pytest.raises(UnsupportedSchemaError):
        assert_importable_schema("99.0.0")
    with pytest.raises(UnsupportedSchemaError):
        parse_schema_version("v1")


def test_verify_checksums_detects_mismatch() -> None:
    sections = {name: [] if name != "project.json" else {"name": "demo"} for name in PACKAGE_SECTION_FILES}
    files = {name: checksum_payload(payload) for name, payload in sections.items()}
    files["characters.json"] = "0" * 64
    with pytest.raises(ValidationError, match="校验和不匹配"):
        verify_checksums(files, sections)
