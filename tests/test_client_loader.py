"""游戏客户端示例加载器测试。不连接编辑器数据库。"""

from pathlib import Path

import pytest

from backend.core.schema_version import FROZEN_CLIENT_SCHEMA_VERSION
from game_data_loader import load_export_dir
from game_data_loader.contract import frozen_schema_version
from game_data_loader.errors import ClientChecksumError, ClientSchemaError
from game_data_loader.sample import SAMPLE_ROOT, write_sample_export


def test_loader_source_does_not_import_backend() -> None:
    root = Path(__file__).resolve().parents[1] / "game_data_loader"
    for path in root.glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                assert "backend" not in stripped, path.name


def test_frozen_contract_matches_editor() -> None:
    assert frozen_schema_version() == FROZEN_CLIENT_SCHEMA_VERSION == "1.12.0"


def test_load_sample_export(tmp_path: Path) -> None:
    root = write_sample_export(tmp_path / "export")
    data = load_export_dir(root)
    liu = data.character_by_code("chr_liu_bei")
    assert liu.name == "刘备"
    assert liu.courtesy_name == "玄德"
    assert liu.force == 72
    assert data.schema_version == "1.12.0"
    assert data.project_code == "proj_sample"


def test_committed_sample_export_loads() -> None:
    write_sample_export(SAMPLE_ROOT)
    data = load_export_dir(SAMPLE_ROOT)
    assert data.character_by_code("chr_liu_bei").name == "刘备"


def test_reject_wrong_schema(tmp_path: Path) -> None:
    root = write_sample_export(tmp_path / "export")
    manifest = (root / "manifest.json").read_text(encoding="utf-8").replace("1.12.0", "1.11.0")
    (root / "manifest.json").write_text(manifest, encoding="utf-8")
    with pytest.raises(ClientSchemaError):
        load_export_dir(root)


def test_reject_tampered_checksum(tmp_path: Path) -> None:
    root = write_sample_export(tmp_path / "export")
    (root / "characters.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ClientChecksumError):
        load_export_dir(root)
