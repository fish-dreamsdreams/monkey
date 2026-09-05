"""项目导入导出应用服务。

职责：校验通过后生成客户端可读包，并把包导入为新的工作库项目。
写服务不依赖本模块；本模块读取各域服务。
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from backend.core.clock import utc_now
from backend.core.exceptions import ExportBlockedError, ValidationError
from backend.core.paths import project_assets_dir, project_export_dir
from backend.core.schema_version import CURRENT_SCHEMA_VERSION
from backend.domain.export_rules import (
    PACKAGE_SECTION_FILES,
    assert_importable_schema,
    checksum_payload,
    verify_checksums,
)
from backend.schemas.asset import CharacterPresentationWrite, ModelAssetWrite, ResourceWrite
from backend.schemas.character import CharacterCreate, PersonalityTagRead
from backend.schemas.city import CityWrite
from backend.schemas.event import EventFactionWrite, EventParticipantWrite, EventSourceWrite, EventWrite
from backend.schemas.export import ExportManifest, ExportPackage, ExportResult
from backend.schemas.faction import FactionMemberWrite, FactionTerritoryWrite, FactionWrite
from backend.schemas.map import MapCityPlace, MapFeatureWrite, MapWrite, TerrainCellPatch, TerrainPatchWrite
from backend.schemas.personality import PersonalityTagCreate
from backend.schemas.project import ProjectCreate, ProjectRead
from backend.schemas.relationship import RelationshipCreate
from backend.schemas.skill import CharacterSkillWrite, SkillWrite
from backend.schemas.source import CharacterSourceWrite, SourceCreate
from backend.schemas.story import (
    StoryActionWrite,
    StoryCastWrite,
    StoryChapterWrite,
    StoryChoiceWrite,
    StoryConditionWrite,
    StoryEdgeWrite,
    StoryNodeWrite,
    StoryWrite,
)
from backend.services.asset_service import AssetService
from backend.services.character_service import CharacterService
from backend.services.city_service import CityService
from backend.services.event_service import EventService
from backend.services.faction_service import FactionService
from backend.services.map_service import MapService
from backend.services.project_service import ProjectService
from backend.services.relationship_service import RelationshipService
from backend.services.skill_service import SkillService
from backend.services.source_service import SourceService
from backend.services.story_service import StoryService
from backend.services.validation_service import ValidationService
from backend.validation.types import IssueSeverity, ValidationMode


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _remap(old: str | None, table: dict[str, str], field: str) -> str | None:
    if old is None:
        return None
    mapped = table.get(old)
    if mapped is None:
        raise ValidationError(f"导出包引用了未知 ID: {old}", field=field)
    return mapped


def _must(old: str, table: dict[str, str], field: str) -> str:
    mapped = _remap(old, table, field)
    if mapped is None:
        raise ValidationError("缺少必填 ID", field=field)
    return mapped


class ExportService:
    """导出冻结包 / 导入新项目。"""

    def __init__(
        self,
        projects: ProjectService,
        sources: SourceService,
        characters: CharacterService,
        relationships: RelationshipService,
        skills: SkillService,
        cities: CityService,
        factions: FactionService,
        maps: MapService,
        events: EventService,
        stories: StoryService,
        assets: AssetService,
        validation: ValidationService,
    ) -> None:
        self._projects = projects
        self._sources = sources
        self._characters = characters
        self._relationships = relationships
        self._skills = skills
        self._cities = cities
        self._factions = factions
        self._maps = maps
        self._events = events
        self._stories = stories
        self._assets = assets
        self._validation = validation

    async def export_project(
        self,
        project_id: str,
        mode: ValidationMode = ValidationMode.STRICT_HISTORICAL,
    ) -> ExportResult:
        """校验通过后写出客户端包。"""
        project = await self._projects.get(project_id)
        report = await self._validation.validate(project_id, mode)
        if not report.valid:
            details = [
                {
                    "field": issue.rule,
                    "message": f"{issue.entity_type}:{issue.entity_id} {issue.message}",
                }
                for issue in report.issues
                if issue.severity == IssueSeverity.ERROR
            ]
            raise ExportBlockedError(details)
        package = await self._build_package(project, mode)
        export_dir = self._write_files(project.id, project.content_version, package)
        return ExportResult(export_dir=str(export_dir), package=package)

    async def import_package(self, package: ExportPackage) -> ProjectRead:
        """校验 schema 与 checksum 后导入为新项目。实体 ID 重新生成。"""
        assert_importable_schema(package.manifest.schema_version)
        verify_checksums(package.manifest.files, package.section_payloads())
        ids: dict[str, str] = {}
        project = await self._import_project(package.project)
        await self._import_tags(project.id, package.personality_tags)
        await self._import_sources(project.id, package.sources)
        await self._import_characters(project.id, package.characters, ids)
        await self._import_relationships(project.id, package.relationships, ids)
        await self._import_skills(project.id, package.skills, ids)
        await self._import_character_skills(project.id, package.character_skills, ids)
        await self._import_maps(project.id, package.maps, ids)
        await self._import_cities(project.id, package.cities, ids)
        await self._place_cities(project.id, package.maps, ids)
        await self._import_factions(project.id, package.factions, ids)
        await self._import_events(project.id, package.events, ids)
        await self._import_stories(project.id, package.stories, ids)
        await self._import_resources(project.id, package.resources, ids)
        await self._import_presentations(project.id, package.characters, ids)
        return await self._projects.get(project.id)

    async def _build_package(self, project: ProjectRead, mode: ValidationMode) -> ExportPackage:
        characters = await self._load_characters(project.id)
        skills = [_dump(item) for item in await self._skills.list_skills(project.id)]
        maps: list[dict[str, Any]] = []
        for summary in await self._maps.list_maps(project.id):
            detail = await self._maps.get(project.id, summary.id)
            terrain = [_dump(cell) for cell in await self._maps.list_terrain(project.id, summary.id)]
            maps.append({"map": _dump(detail), "terrain": terrain})
        factions: list[dict[str, Any]] = []
        for faction in await self._factions.list_factions(project.id):
            factions.append(
                {
                    "faction": _dump(faction),
                    "members": [_dump(item) for item in await self._factions.list_members(project.id, faction.id)],
                    "territories": [
                        _dump(item) for item in await self._factions.list_territories(project.id, faction.id)
                    ],
                }
            )
        events = []
        for summary in await self._events.list_events(project.id):
            events.append(_dump(await self._events.get(project.id, summary.id)))
        stories = []
        for summary in await self._stories.list_stories(project.id):
            stories.append(_dump(await self._stories.get(project.id, summary.id)))
        character_skills: list[dict[str, Any]] = []
        for character in characters:
            for binding in await self._skills.list_character_skills(project.id, character["id"]):
                character_skills.append(_dump(binding))
        payload = ExportPackage(
            manifest=ExportManifest(
                schema_version=CURRENT_SCHEMA_VERSION,
                content_version=project.content_version,
                exported_at=utc_now(),
                validation_mode=mode,
                project_code=project.code,
                project_name=project.name,
                files={name: "" for name in PACKAGE_SECTION_FILES},
            ),
            project={
                "code": project.code,
                "name": project.name,
                "description": project.description,
                "target_start_year": project.target_start_year,
                "target_end_year": project.target_end_year,
                "schema_version": CURRENT_SCHEMA_VERSION,
                "content_version": project.content_version,
            },
            personality_tags=[
                _dump(PersonalityTagRead.model_validate(tag))
                for tag in await self._projects.list_personality_tags(project.id)
            ],
            sources=[_dump(item) for item in await self._sources.list_sources(project.id)],
            characters=characters,
            relationships=[_dump(item) for item in await self._relationships.list_relationships(project.id)],
            skills=skills,
            character_skills=character_skills,
            maps=maps,
            cities=[_dump(item) for item in await self._cities.list_cities(project.id)],
            factions=factions,
            events=events,
            stories=stories,
            resources=self._load_resources(project.id, await self._assets.list_resources(project.id)),
        )
        files = {name: checksum_payload(section) for name, section in payload.section_payloads().items()}
        payload.manifest.files = files
        return payload

    async def _load_characters(self, project_id: str) -> list[dict[str, Any]]:
        skip = 0
        limit = 200
        collected: list[dict[str, Any]] = []
        while True:
            items, total = await self._characters.list_characters(project_id, skip, limit)
            for summary in items:
                collected.append(_dump(await self._characters.get(project_id, summary.id)))
            skip += limit
            if skip >= total:
                break
        return collected

    def _load_resources(self, project_id: str, resources: list[Any]) -> list[dict[str, Any]]:
        root = project_assets_dir(project_id)
        dumped: list[dict[str, Any]] = []
        for resource in resources:
            item = _dump(resource)
            path = root / resource.path
            item["content_base64"] = (
                base64.b64encode(path.read_bytes()).decode("ascii") if path.is_file() else None
            )
            dumped.append(item)
        return dumped

    def _write_files(self, project_id: str, content_version: int, package: ExportPackage) -> Path:
        root = project_export_dir(project_id, content_version)
        root.mkdir(parents=True, exist_ok=True)
        for name, payload in package.section_payloads().items():
            (root / name).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        (root / "manifest.json").write_text(
            json.dumps(_dump(package.manifest), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return root

    async def _import_project(self, section: dict[str, Any]) -> ProjectRead:
        name = str(section.get("name") or "").strip()
        if not name:
            raise ValidationError("导出包缺少项目名称", field="project")
        code = section.get("code")
        if isinstance(code, str) and code.strip():
            existing = await self._projects.list_projects()
            if any(item.code == code.strip().lower() for item in existing):
                code = None
        else:
            code = None
        return await self._projects.create(
            ProjectCreate(
                name=name,
                code=code,
                description=section.get("description"),
                target_start_year=section.get("target_start_year"),
                target_end_year=section.get("target_end_year"),
            )
        )

    async def _import_tags(self, project_id: str, tags: list[dict[str, Any]]) -> None:
        existing = {tag.code for tag in await self._projects.list_personality_tags(project_id)}
        for tag in tags:
            if tag.get("is_system") or tag.get("code") in existing:
                continue
            await self._projects.create_personality_tag(
                project_id,
                PersonalityTagCreate(
                    code=tag["code"],
                    name=tag["name"],
                    description=tag.get("description"),
                ),
            )

    async def _import_sources(self, project_id: str, sources: list[dict[str, Any]]) -> None:
        existing = {item.code for item in await self._sources.list_sources(project_id)}
        for source in sources:
            if source.get("is_system") or source.get("code") in existing:
                continue
            await self._sources.create(
                project_id,
                SourceCreate(code=source["code"], name=source["name"], source_type=source["source_type"]),
            )

    async def _import_characters(
        self, project_id: str, characters: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in characters:
            sources = [
                CharacterSourceWrite(
                    source_code=citation["source_code"],
                    bound_layer=citation["bound_layer"],
                    quotation=citation.get("quotation"),
                    reference=citation.get("reference"),
                    note=citation.get("note"),
                )
                for citation in item.get("sources") or []
            ]
            created = await self._characters.create(
                project_id,
                CharacterCreate(
                    base=item["base"],
                    historical=item.get("historical") or {},
                    game=item.get("game") or {},
                    sources=sources,
                ),
            )
            ids[item["id"]] = created.id

    async def _import_relationships(
        self, project_id: str, relationships: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in relationships:
            await self._relationships.create(
                project_id,
                RelationshipCreate(
                    from_character_id=_must(item["from_character"]["id"], ids, "from_character_id"),
                    to_character_id=_must(item["to_character"]["id"], ids, "to_character_id"),
                    relationship_type=item["relationship_type"],
                    intimacy=item.get("intimacy", 50),
                    hostility=item.get("hostility", 0),
                    start_year=item.get("start_year"),
                    end_year=item.get("end_year"),
                    note=item.get("note"),
                ),
            )

    async def _import_skills(self, project_id: str, skills: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in skills:
            payload = {key: value for key, value in item.items() if key not in {"id", "project_id"}}
            created = await self._skills.create(project_id, SkillWrite.model_validate(payload))
            ids[item["id"]] = created.id

    async def _import_character_skills(
        self, project_id: str, bindings: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in bindings:
            await self._skills.bind(
                project_id,
                _must(item["character_id"], ids, "character_id"),
                CharacterSkillWrite(
                    skill_id=_must(item["skill"]["id"], ids, "skill_id"),
                    level=item.get("level", 1),
                    source_note=item.get("source_note"),
                ),
            )

    async def _import_maps(self, project_id: str, maps: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in maps:
            meta = item["map"]
            created = await self._maps.create(
                project_id,
                MapWrite(
                    code=meta["code"],
                    name=meta["name"],
                    width=meta["width"],
                    height=meta["height"],
                    cell_size=meta.get("cell_size", 32),
                    default_terrain=meta["default_terrain"],
                    description=meta.get("description"),
                ),
            )
            ids[meta["id"]] = created.id
            cells = [
                TerrainCellPatch(x=cell["x"], y=cell["y"], terrain=cell["terrain"])
                for cell in item.get("terrain") or []
            ]
            if cells:
                await self._maps.patch_terrain(project_id, created.id, TerrainPatchWrite(cells=cells))
            for feature in meta.get("features") or []:
                saved = await self._maps.add_feature(
                    project_id,
                    created.id,
                    MapFeatureWrite(
                        code=feature["code"],
                        name=feature["name"],
                        feature_type=feature["feature_type"],
                        points=feature["points"],
                        note=feature.get("note"),
                    ),
                )
                ids[feature["id"]] = saved.id

    async def _import_cities(self, project_id: str, cities: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in cities:
            created = await self._cities.create(
                project_id,
                CityWrite(
                    code=item["code"],
                    name=item["name"],
                    coord_x=item.get("coord_x"),
                    coord_y=item.get("coord_y"),
                    historical=item.get("historical") or {},
                    game=item.get("game") or {},
                ),
            )
            ids[item["id"]] = created.id

    async def _place_cities(self, project_id: str, maps: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in maps:
            meta = item["map"]
            map_id = _must(meta["id"], ids, "map_id")
            for city in meta.get("cities") or []:
                await self._maps.place_city(
                    project_id,
                    map_id,
                    MapCityPlace(
                        city_id=_must(city["id"], ids, "city_id"),
                        coord_x=city["coord_x"],
                        coord_y=city["coord_y"],
                    ),
                )

    async def _import_factions(
        self, project_id: str, factions: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in factions:
            meta = item["faction"]
            leader_id = _remap((meta.get("leader") or {}).get("id"), ids, "leader_character_id")
            capital_id = _remap((meta.get("capital") or {}).get("id"), ids, "capital_city_id")
            created = await self._factions.create(
                project_id,
                FactionWrite(
                    code=meta["code"],
                    name=meta["name"],
                    color=meta.get("color", "#808080"),
                    leader_character_id=leader_id,
                    capital_city_id=capital_id,
                    start_year=meta.get("start_year"),
                    end_year=meta.get("end_year"),
                    historical_description=meta.get("historical_description"),
                ),
            )
            ids[meta["id"]] = created.id
            for member in item.get("members") or []:
                await self._factions.add_member(
                    project_id,
                    created.id,
                    FactionMemberWrite(
                        character_id=_must(member["character"]["id"], ids, "character_id"),
                        role=member["role"],
                        start_year=member.get("start_year"),
                        end_year=member.get("end_year"),
                        note=member.get("note"),
                    ),
                )
            for territory in item.get("territories") or []:
                await self._factions.add_territory(
                    project_id,
                    created.id,
                    FactionTerritoryWrite(
                        city_id=_must(territory["city"]["id"], ids, "city_id"),
                        start_year=territory.get("start_year"),
                        end_year=territory.get("end_year"),
                        note=territory.get("note"),
                    ),
                )

    async def _import_events(self, project_id: str, events: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in events:
            location_id = _remap((item.get("location") or {}).get("id"), ids, "location_city_id")
            created = await self._events.create(
                project_id,
                EventWrite(
                    code=item["code"],
                    name=item["name"],
                    event_type=item.get("event_type", "other"),
                    layer=item.get("layer", "historical"),
                    year=item["year"],
                    month=item.get("month"),
                    day=item.get("day"),
                    location_city_id=location_id,
                    location_note=item.get("location_note"),
                    description=item.get("description"),
                    consequences=item.get("consequences"),
                ),
            )
            ids[item["id"]] = created.id
            for participant in item.get("participants") or []:
                await self._events.add_participant(
                    project_id,
                    created.id,
                    EventParticipantWrite(
                        character_id=_must(participant["character"]["id"], ids, "character_id"),
                        role=participant.get("role", "participant"),
                        note=participant.get("note"),
                    ),
                )
            for faction in item.get("factions") or []:
                await self._events.add_faction(
                    project_id,
                    created.id,
                    EventFactionWrite(
                        faction_id=_must(faction["faction"]["id"], ids, "faction_id"),
                        role=faction.get("role", "involved"),
                        note=faction.get("note"),
                    ),
                )
            for source in item.get("sources") or []:
                await self._events.add_source(
                    project_id,
                    created.id,
                    EventSourceWrite(
                        source_code=source["source_code"],
                        quotation=source.get("quotation"),
                        reference=source.get("reference"),
                        note=source.get("note"),
                    ),
                )

    async def _import_stories(self, project_id: str, stories: list[dict[str, Any]], ids: dict[str, str]) -> None:
        for item in stories:
            created = await self._stories.create(
                project_id,
                StoryWrite(
                    code=item["code"],
                    name=item["name"],
                    layer=item.get("layer", "literary"),
                    description=item.get("description"),
                ),
            )
            ids[item["id"]] = created.id
            for chapter in item.get("chapters") or []:
                saved = await self._stories.add_chapter(
                    project_id,
                    created.id,
                    StoryChapterWrite(
                        code=chapter["code"],
                        name=chapter["name"],
                        sort_order=chapter.get("sort_order", 0),
                        summary=chapter.get("summary"),
                    ),
                )
                ids[chapter["id"]] = saved.id
            for node in item.get("nodes") or []:
                saved = await self._stories.add_node(
                    project_id,
                    created.id,
                    StoryNodeWrite(
                        code=node["code"],
                        name=node["name"],
                        node_type=node["node_type"],
                        chapter_id=_remap(node.get("chapter_id"), ids, "chapter_id"),
                        is_entry=node.get("is_entry", False),
                        is_ending=node.get("is_ending", False),
                        sort_order=node.get("sort_order", 0),
                        title=node.get("title"),
                        body=node.get("body"),
                        event_id=_remap((node.get("event") or {}).get("id"), ids, "event_id"),
                        character_id=_remap((node.get("character") or {}).get("id"), ids, "character_id"),
                        city_id=_remap((node.get("city") or {}).get("id"), ids, "city_id"),
                        faction_id=_remap((node.get("faction") or {}).get("id"), ids, "faction_id"),
                    ),
                )
                ids[node["id"]] = saved.id
            for node in item.get("nodes") or []:
                node_id = _must(node["id"], ids, "node_id")
                for condition in node.get("conditions") or []:
                    await self._stories.add_condition(
                        project_id,
                        created.id,
                        node_id,
                        StoryConditionWrite(
                            condition_type=condition["condition_type"],
                            expression=condition.get("expression"),
                            note=condition.get("note"),
                        ),
                    )
                for action in node.get("actions") or []:
                    await self._stories.add_action(
                        project_id,
                        created.id,
                        node_id,
                        StoryActionWrite(
                            action_type=action["action_type"],
                            expression=action.get("expression"),
                            note=action.get("note"),
                        ),
                    )
                for cast in node.get("cast") or []:
                    await self._stories.add_cast(
                        project_id,
                        created.id,
                        node_id,
                        StoryCastWrite(
                            character_id=_must(cast["character"]["id"], ids, "character_id"),
                            role=cast.get("role", "present"),
                            note=cast.get("note"),
                        ),
                    )
                edge_by_choice = {
                    edge["choice_id"]: edge for edge in node.get("outgoing") or [] if edge.get("choice_id")
                }
                for choice in node.get("choices") or []:
                    if not choice.get("to_node_id"):
                        continue
                    linked = edge_by_choice.get(choice["id"], {})
                    await self._stories.add_choice(
                        project_id,
                        created.id,
                        node_id,
                        StoryChoiceWrite(
                            label=choice["label"],
                            to_node_id=_must(choice["to_node_id"], ids, "to_node_id"),
                            is_conditional=linked.get("is_conditional", False),
                            condition_note=linked.get("condition_note"),
                            sort_order=choice.get("sort_order", 0),
                        ),
                    )
                for edge in node.get("outgoing") or []:
                    if edge.get("choice_id"):
                        continue
                    await self._stories.add_edge(
                        project_id,
                        created.id,
                        node_id,
                        StoryEdgeWrite(
                            to_node_id=_must(edge["to_node_id"], ids, "to_node_id"),
                            is_conditional=edge.get("is_conditional", False),
                            condition_note=edge.get("condition_note"),
                            sort_order=edge.get("sort_order", 0),
                        ),
                    )

    async def _import_resources(
        self, project_id: str, resources: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in resources:
            model = None
            if item.get("model"):
                model = ModelAssetWrite(
                    mesh_format=item["model"]["mesh_format"],
                    lod_count=item["model"].get("lod_count", 1),
                    animation_set_note=item["model"].get("animation_set_note"),
                    skeleton_note=item["model"].get("skeleton_note"),
                )
            created = await self._assets.create(
                project_id,
                ResourceWrite(
                    code=item["code"],
                    name=item["name"],
                    resource_type=item["resource_type"],
                    path=item["path"],
                    checksum=None,
                    mime_type=item.get("mime_type"),
                    preview_path=item.get("preview_path"),
                    note=item.get("note"),
                    content_base64=item.get("content_base64"),
                    model=model,
                ),
            )
            ids[item["id"]] = created.id

    async def _import_presentations(
        self, project_id: str, characters: list[dict[str, Any]], ids: dict[str, str]
    ) -> None:
        for item in characters:
            presentation = item.get("presentation") or {}
            portrait = (presentation.get("portrait") or {}).get("id")
            model = (presentation.get("model") or {}).get("id")
            if not portrait and not model:
                continue
            await self._assets.bind_character_presentation(
                project_id,
                _must(item["id"], ids, "character_id"),
                CharacterPresentationWrite(
                    portrait_id=_remap(portrait, ids, "portrait_id"),
                    model_id=_remap(model, ids, "model_id"),
                ),
            )
