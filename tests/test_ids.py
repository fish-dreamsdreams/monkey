"""实体 ID 规则测试。"""

import pytest

from backend.cli import build_parser
from backend.core.alembic_runtime import script_head_revision
from backend.core.exceptions import InvalidIdError
from backend.core.ids import EntityPrefix, new_id, require_id


def test_new_id_uses_prefix_and_fixed_length() -> None:
    value = new_id(EntityPrefix.PROJECT)
    assert value.startswith("prj_")
    assert len(value) == 36
    require_id(value, EntityPrefix.PROJECT, field="project_id")


def test_require_id_rejects_plain_uuid() -> None:
    with pytest.raises(InvalidIdError) as exc:
        require_id("11111111-1111-1111-1111-111111111111", EntityPrefix.PROJECT, field="project_id")
    assert exc.value.field == "project_id"


def test_require_id_rejects_wrong_prefix() -> None:
    character_id = new_id(EntityPrefix.CHARACTER)
    with pytest.raises(InvalidIdError):
        require_id(character_id, EntityPrefix.PROJECT, field="project_id")


def test_cli_parses_db_commands() -> None:
    parser = build_parser()
    args = parser.parse_args(["db", "check"])
    assert args.command == "db"
    assert args.db_command == "check"


def test_alembic_script_head_is_phase2() -> None:
    assert script_head_revision() == "0002_phase2"
