"""读取冻结合同。不依赖 backend 包。"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from game_data_loader.errors import ClientChecksumError, ClientSchemaError

_REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = _REPO_ROOT / "packages" / "game-data-schema"
FROZEN_CONTRACT_PATH = SCHEMA_ROOT / "frozen.json"


@lru_cache(maxsize=1)
def load_frozen_contract() -> dict[str, Any]:
    """加载 packages/game-data-schema/frozen.json。"""
    return json.loads(FROZEN_CONTRACT_PATH.read_text(encoding="utf-8"))


def frozen_schema_version() -> str:
    """客户端唯一接受的数据包版本。"""
    return str(load_frozen_contract()["schema_version"])


def package_files() -> tuple[str, ...]:
    """冻结分区文件名。"""
    return tuple(load_frozen_contract()["files"])


def canonical_json(payload: object) -> str:
    """稳定 JSON，供 checksum。"""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum_payload(payload: object) -> str:
    """对分区内容做 SHA-256。"""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def assert_frozen_schema(schema_version: str) -> None:
    """客户端只加载冻结版本，不接受更旧或更新的包。"""
    expected = frozen_schema_version()
    if schema_version != expected:
        raise ClientSchemaError(f"客户端只支持 schema {expected}，收到 {schema_version}")


def verify_checksums(files: dict[str, str], sections: dict[str, object]) -> None:
    """核对 manifest.files 与分区内容。"""
    expected = set(package_files())
    if set(files) != expected or set(sections) != expected:
        raise ClientChecksumError("manifest.files 与数据包分区不一致")
    for name, payload in sections.items():
        digest = checksum_payload(payload)
        if files.get(name) != digest:
            raise ClientChecksumError(f"校验和不匹配: {name}")
