"""写入官方示例导出包。仅用于仓库夹具，不是游戏运行时存档。"""

from __future__ import annotations

import json
from pathlib import Path

from game_data_loader.contract import checksum_payload, frozen_schema_version, package_files

SAMPLE_ROOT = Path(__file__).resolve().parents[1] / "data" / "sample-export"


def sample_sections() -> dict[str, object]:
    """最小可加载示例：含刘备，其余分区为空。"""
    sections: dict[str, object] = {name: [] for name in package_files()}
    sections["project.json"] = {
        "code": "proj_sample",
        "name": "示例内容包",
        "description": "供客户端加载器验收，不是运行时存档。",
        "target_start_year": 184,
        "target_end_year": 280,
        "schema_version": frozen_schema_version(),
        "content_version": 1,
    }
    sections["characters.json"] = [
        {
            "id": "chr_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
            "project_id": "prj_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
            "base": {
                "code": "chr_liu_bei",
                "name": "刘备",
                "courtesy_name": "玄德",
                "gender": "male",
                "birth_year": 161,
                "death_year": 223,
                "birthplace": "涿郡涿县",
                "ethnicity": "汉",
                "identity": "蜀汉开国皇帝",
            },
            "historical": {
                "biography": "东汉末年幽州涿郡人，蜀汉开国皇帝。",
                "family_background": None,
                "life_experience": None,
                "achievements": None,
                "historical_evaluation": None,
            },
            "game": {
                "force": 72,
                "intelligence": 80,
                "politics": 85,
                "charisma": 95,
                "leadership": 86,
                "stamina": 78,
                "morale": 90,
                "mobility": 70,
                "personality_tag_codes": ["benevolent"],
                "attribute_version": "default",
            },
            "personalities": [],
            "sources": [],
            "presentation": {"portrait": None, "model": None},
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    return sections


def write_sample_export(root: Path | None = None) -> Path:
    """写出 manifest 与分区文件。"""
    target = root or SAMPLE_ROOT
    target.mkdir(parents=True, exist_ok=True)
    sections = sample_sections()
    files = {name: checksum_payload(payload) for name, payload in sections.items()}
    manifest = {
        "schema_version": frozen_schema_version(),
        "content_version": 1,
        "exported_at": "2026-01-01T00:00:00+00:00",
        "validation_mode": "strict_historical",
        "project_code": "proj_sample",
        "project_name": "示例内容包",
        "files": files,
    }
    for name, payload in sections.items():
        (target / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target
