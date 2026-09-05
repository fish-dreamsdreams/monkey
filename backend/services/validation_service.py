"""校验应用服务。

职责：把各域读成快照后交给 ValidationEngine。写人物/剧情/势力时不得依赖本服务。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.paths import project_assets_dir
from backend.domain.asset_rules import resolve_asset_file
from backend.domain.story_rules import GraphEdge, GraphNode
from backend.repositories.asset_repository import AssetRepository
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.event_repository import EventRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.relationship_repository import RelationshipRepository
from backend.repositories.story_repository import StoryRepository
from backend.schemas.validation import ValidationIssueRead, ValidationReportRead
from backend.validation.engine import validate_project
from backend.validation.snapshots import (
    CharacterSnap,
    CitySnap,
    EventFactionSnap,
    EventParticipantSnap,
    EventSnap,
    FactionSnap,
    MemberSnap,
    ProjectSnapshot,
    RelationshipSnap,
    ResourceSnap,
    StorySnap,
    TerritorySnap,
)
from backend.validation.types import ValidationMode


class ValidationService:
    """项目级只读校验。"""

    def __init__(
        self,
        characters: CharacterRepository,
        cities: CityRepository,
        factions: FactionRepository,
        events: EventRepository,
        relationships: RelationshipRepository,
        stories: StoryRepository,
        assets: AssetRepository,
        projects: ProjectRepository,
    ) -> None:
        self._characters = characters
        self._cities = cities
        self._factions = factions
        self._events = events
        self._relationships = relationships
        self._stories = stories
        self._assets = assets
        self._projects = projects

    async def validate(self, project_id: str, mode: ValidationMode) -> ValidationReportRead:
        """运行跨实体校验并返回报告。始终 200，用 valid 表示能否导出。"""
        if await self._projects.get(project_id) is None:
            raise NotFoundError("项目不存在")
        snapshot = await self._load_snapshot(project_id)
        report = validate_project(snapshot, mode)
        issues = [
            ValidationIssueRead(
                rule=item.rule,
                severity=item.severity,
                message=item.message,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                field=item.field,
            )
            for item in report.issues
        ]
        return ValidationReportRead(
            mode=mode,
            valid=report.valid,
            error_count=len(report.errors),
            warning_count=len(report.warnings),
            issues=issues,
        )

    async def _load_snapshot(self, project_id: str) -> ProjectSnapshot:
        characters, _total = await self._characters.list_by_project(project_id, skip=0, limit=5000)
        cities = await self._cities.list_by_project(project_id)
        factions = await self._factions.list_by_project(project_id)
        events = await self._events.list_for_validation(project_id)
        territories = await self._factions.list_all_territories(project_id)
        members = await self._factions.list_all_members(project_id)
        relationships = await self._relationships.list_primary(project_id)
        stories = await self._stories.list_by_project(project_id)
        resources = await self._assets.list_by_project(project_id)
        root = project_assets_dir(project_id)
        return ProjectSnapshot(
            characters=[
                CharacterSnap(
                    id=item.id,
                    name=item.name,
                    birth_year=item.birth_year,
                    death_year=item.death_year,
                )
                for item in characters
            ],
            cities=[
                CitySnap(
                    id=item.id,
                    name=item.name,
                    founded_year=item.founded_year,
                    destroyed_year=item.destroyed_year,
                )
                for item in cities
            ],
            factions=[
                FactionSnap(
                    id=item.id,
                    name=item.name,
                    start_year=item.start_year,
                    end_year=item.end_year,
                )
                for item in factions
            ],
            events=[
                EventSnap(
                    id=item.id,
                    name=item.name,
                    year=item.year,
                    layer=item.layer,
                    location_city_id=item.location_city_id,
                    participants=tuple(
                        EventParticipantSnap(
                            character_id=part.character_id,
                            character_name=part.character.name if part.character is not None else part.character_id,
                            birth_year=part.character.birth_year if part.character is not None else None,
                            death_year=part.character.death_year if part.character is not None else None,
                        )
                        for part in item.participants
                    ),
                    factions=tuple(
                        EventFactionSnap(
                            faction_id=row.faction_id,
                            faction_name=row.faction.name if row.faction is not None else row.faction_id,
                            start_year=row.faction.start_year if row.faction is not None else None,
                            end_year=row.faction.end_year if row.faction is not None else None,
                        )
                        for row in item.factions
                    ),
                    source_types=tuple(
                        row.source.source_type for row in item.sources if row.source is not None
                    ),
                )
                for item in events
            ],
            territories=[
                TerritorySnap(
                    id=item.id,
                    city_id=item.city_id,
                    city_name=item.city.name if item.city is not None else item.city_id,
                    faction_id=item.faction_id,
                    faction_name=item.faction.name if item.faction is not None else item.faction_id,
                    start_year=item.start_year,
                    end_year=item.end_year,
                )
                for item in territories
            ],
            members=[
                MemberSnap(
                    id=item.id,
                    character_id=item.character_id,
                    character_name=item.character.name if item.character is not None else item.character_id,
                    faction_id=item.faction_id,
                    faction_name=item.faction.name if item.faction is not None else item.faction_id,
                    start_year=item.start_year,
                    end_year=item.end_year,
                    birth_year=item.character.birth_year if item.character is not None else None,
                    death_year=item.character.death_year if item.character is not None else None,
                )
                for item in members
            ],
            relationships=[
                RelationshipSnap(
                    id=item.id,
                    from_id=item.from_character_id,
                    to_id=item.to_character_id,
                    from_birth=item.from_character.birth_year if item.from_character is not None else None,
                    from_death=item.from_character.death_year if item.from_character is not None else None,
                    to_birth=item.to_character.birth_year if item.to_character is not None else None,
                    to_death=item.to_character.death_year if item.to_character is not None else None,
                    start_year=item.start_year,
                    end_year=item.end_year,
                )
                for item in relationships
            ],
            stories=[
                StorySnap(
                    id=item.id,
                    name=item.name,
                    nodes=tuple(
                        GraphNode(id=node.id, is_entry=node.is_entry, is_ending=node.is_ending)
                        for node in item.nodes
                    ),
                    edges=tuple(
                        GraphEdge(
                            from_id=edge.from_node_id,
                            to_id=edge.to_node_id,
                            is_conditional=edge.is_conditional,
                            has_terminator=bool(edge.condition_note and edge.condition_note.strip()),
                        )
                        for node in item.nodes
                        for edge in node.outgoing
                    ),
                )
                for item in stories
            ],
            resources=[_resource_snap(item.id, item.name, item.path, item.checksum, root) for item in resources],
        )


def _resource_snap(resource_id: str, name: str, relative: str, checksum: str, root: Path) -> ResourceSnap:
    exists = False
    checksum_ok = False
    try:
        full = resolve_asset_file(root, relative)
        exists = full.is_file()
        if exists:
            checksum_ok = hashlib.sha256(full.read_bytes()).hexdigest() == checksum
    except ValidationError:
        exists = False
    return ResourceSnap(id=resource_id, name=name, path=relative, exists=exists, checksum_ok=checksum_ok)
