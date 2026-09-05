"""项目导入导出规则。

职责：规范客户端数据包分区、canonical checksum，以及 schema 兼容性。
分区文件列表以 packages/game-data-schema/frozen.json 为准。
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any

from backend.core.exceptions import UnsupportedSchemaError, ValidationError
from backend.core.paths import REPO_ROOT
from backend.core.schema_version import CURRENT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS

FROZEN_CONTRACT_PATH = REPO_ROOT / "packages" / "game-data-schema" / "frozen.json"


@lru_cache(maxsize=1)
def load_frozen_contract() -> dict[str, Any]:
    """读取冻结合同。"""
    return json.loads(FROZEN_CONTRACT_PATH.read_text(encoding="utf-8"))


def frozen_client_schema_version() -> str:
    """游戏客户端冻结的数据包版本。"""
    return str(load_frozen_contract()["schema_version"])


PACKAGE_SECTION_FILES: tuple[str, ...] = tuple(load_frozen_contract()["files"])


def canonical_json(payload: object) -> str:
    """稳定 JSON，供 checksum。"""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum_payload(payload: object) -> str:
    """对分区内容做 SHA-256。"""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def parse_schema_version(value: str) -> tuple[int, int, int]:
    """解析三段版本号。"""
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise UnsupportedSchemaError(f"无法解析 schema_version: {value}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def assert_importable_schema(schema_version: str) -> None:
    """导入包必须是当前编辑器认识、且不比当前更新的 schema。"""
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaError(f"不支持的 schema_version: {schema_version}")
    if parse_schema_version(schema_version) > parse_schema_version(CURRENT_SCHEMA_VERSION):
        raise UnsupportedSchemaError("导出包 schema 比当前编辑器更新")


def verify_checksums(files: dict[str, str], sections: dict[str, object]) -> None:
    """核对 manifest.files 与分区内容。"""
    expected = set(PACKAGE_SECTION_FILES)
    actual = set(files)
    if actual != expected:
        raise ValidationError("manifest.files 与数据包分区不一致", field="files")
    missing = expected - set(sections)
    extra = set(sections) - expected
    if missing or extra:
        raise ValidationError("数据包分区与约定文件列表不一致", field="files")
    for name, payload in sections.items():
        digest = checksum_payload(payload)
        if files.get(name) != digest:
            raise ValidationError(f"校验和不匹配: {name}", field="files")
