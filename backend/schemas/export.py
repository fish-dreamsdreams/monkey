"""项目导入导出 Schema。面向客户端的冻结包，不含任务/时间线。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.export_rules import PACKAGE_SECTION_FILES
from backend.validation.types import ValidationMode


class ExportManifest(BaseModel):
    """导出清单：版本、校验模式与分区 checksum。"""

    schema_version: str
    content_version: int
    exported_at: datetime
    validation_mode: ValidationMode
    project_code: str
    project_name: str
    files: dict[str, str]


class ExportPackage(BaseModel):
    """完整数据包。分区与 manifest.files 一一对应。"""

    model_config = ConfigDict(extra="forbid")

    manifest: ExportManifest
    project: dict[str, Any]
    personality_tags: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    characters: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[dict[str, Any]] = Field(default_factory=list)
    character_skills: list[dict[str, Any]] = Field(default_factory=list)
    maps: list[dict[str, Any]] = Field(default_factory=list)
    cities: list[dict[str, Any]] = Field(default_factory=list)
    factions: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    stories: list[dict[str, Any]] = Field(default_factory=list)
    resources: list[dict[str, Any]] = Field(default_factory=list)

    def section_payloads(self) -> dict[str, object]:
        """按约定文件名取出分区，供 checksum 与落盘。"""
        mapping = {
            "project.json": self.project,
            "personality_tags.json": self.personality_tags,
            "sources.json": self.sources,
            "characters.json": self.characters,
            "relationships.json": self.relationships,
            "skills.json": self.skills,
            "character_skills.json": self.character_skills,
            "maps.json": self.maps,
            "cities.json": self.cities,
            "factions.json": self.factions,
            "events.json": self.events,
            "stories.json": self.stories,
            "resources.json": self.resources,
        }
        return {name: mapping[name] for name in PACKAGE_SECTION_FILES}


class ExportResult(BaseModel):
    """导出 API 返回：内存包 + 冻结目录。"""

    export_dir: str
    package: ExportPackage


class ClientSchemaRead(BaseModel):
    """冻结合同摘要。客户端只读此版本，不连编辑器数据库。"""

    schema_version: str
    files: list[str]
    unsupported_files: list[str]
    schema_documents: list[str]
    loader: str
    note: str
