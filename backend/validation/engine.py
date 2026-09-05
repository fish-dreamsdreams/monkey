"""跨实体校验引擎。

职责：时间线、城池易主重叠、剧情死循环。读取快照，不写库，不被写服务依赖。
"""

from __future__ import annotations

from collections import defaultdict

from backend.core.exceptions import ValidationError
from backend.domain.character_rules import validate_lifespan
from backend.domain.event_rules import (
    validate_character_alive_in_year,
    validate_city_exists_in_year,
    validate_faction_exists_in_year,
)
from backend.domain.relationship_types import validate_relationship_years, validate_years_against_lifespan
from backend.domain.source_types import SourceType
from backend.domain.story_rules import analyze_story_graph
from backend.domain.year_range import years_overlap
from backend.validation.snapshots import EventSnap, ProjectSnapshot
from backend.validation.types import IssueSeverity, ValidationIssue, ValidationMode, ValidationReport

LEGEND_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        SourceType.LITERARY.value,
        SourceType.FOLKLORE.value,
        SourceType.TRADITION.value,
        SourceType.GAME_SETTING.value,
    }
)
NARRATIVE_LAYERS: frozenset[str] = frozenset({"literary", "game"})


def validate_project(snapshot: ProjectSnapshot, mode: ValidationMode) -> ValidationReport:
    """扫描整个项目快照，收集错误与警告。"""
    report = ValidationReport(mode=mode)
    _check_lifespans(snapshot, report)
    _check_events(snapshot, report, mode)
    _check_city_ownership(snapshot, report)
    _check_members(snapshot, report)
    _check_relationships(snapshot, report)
    _check_stories(snapshot, report)
    _check_resources(snapshot, report)
    return report


def _issue(
    report: ValidationReport,
    *,
    rule: str,
    message: str,
    entity_type: str,
    entity_id: str | None = None,
    field: str | None = None,
    severity: IssueSeverity = IssueSeverity.ERROR,
) -> None:
    report.issues.append(
        ValidationIssue(
            rule=rule,
            severity=severity,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            field=field,
        )
    )


def _from_validation_error(
    report: ValidationReport,
    exc: ValidationError,
    *,
    rule: str,
    entity_type: str,
    entity_id: str | None,
    severity: IssueSeverity = IssueSeverity.ERROR,
) -> None:
    _issue(
        report,
        rule=rule,
        message=exc.message,
        entity_type=entity_type,
        entity_id=entity_id,
        field=exc.field,
        severity=severity,
    )


def _check_lifespans(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    for character in snapshot.characters:
        try:
            validate_lifespan(character.birth_year, character.death_year)
        except ValidationError as exc:
            _from_validation_error(
                report, exc, rule="lifespan", entity_type="character", entity_id=character.id
            )


def _check_events(snapshot: ProjectSnapshot, report: ValidationReport, mode: ValidationMode) -> None:
    cities = {item.id: item for item in snapshot.cities}
    for event in snapshot.events:
        severity = _lifespan_severity(event, mode)
        if severity is None:
            _issue(
                report,
                rule="event_legend_source",
                message=f"{event.name} 要以传说例外绕过生卒校验，必须标记 source_type",
                entity_type="event",
                entity_id=event.id,
                field="sources",
            )
            severity = IssueSeverity.ERROR
        for participant in event.participants:
            try:
                validate_character_alive_in_year(
                    character_name=participant.character_name,
                    birth_year=participant.birth_year,
                    death_year=participant.death_year,
                    event_year=event.year,
                )
            except ValidationError as exc:
                _from_validation_error(
                    report,
                    exc,
                    rule="event_participant_alive",
                    entity_type="event",
                    entity_id=event.id,
                    severity=severity,
                )
        for involved in event.factions:
            try:
                validate_faction_exists_in_year(
                    faction_name=involved.faction_name,
                    start_year=involved.start_year,
                    end_year=involved.end_year,
                    event_year=event.year,
                )
            except ValidationError as exc:
                _from_validation_error(
                    report, exc, rule="event_faction_exists", entity_type="event", entity_id=event.id
                )
        if event.location_city_id:
            city = cities.get(event.location_city_id)
            if city is None:
                _issue(
                    report,
                    rule="event_city_exists",
                    message=f"{event.name} 引用的地点城池不存在",
                    entity_type="event",
                    entity_id=event.id,
                    field="location_city_id",
                )
            else:
                try:
                    validate_city_exists_in_year(
                        city_name=city.name,
                        founded_year=city.founded_year,
                        destroyed_year=city.destroyed_year,
                        event_year=event.year,
                    )
                except ValidationError as exc:
                    _from_validation_error(
                        report, exc, rule="event_city_exists", entity_type="event", entity_id=event.id
                    )


def _lifespan_severity(event: EventSnap, mode: ValidationMode) -> IssueSeverity | None:
    """返回生卒冲突的级别。None 表示想走传说例外但未标注来源。"""
    if mode == ValidationMode.STRICT_HISTORICAL:
        return IssueSeverity.ERROR
    has_legend_source = any(item in LEGEND_SOURCE_TYPES for item in event.source_types)
    if event.layer in NARRATIVE_LAYERS or has_legend_source:
        if not event.source_types:
            return None
        return IssueSeverity.WARNING
    return IssueSeverity.ERROR


def _check_city_ownership(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    by_city: dict[str, list] = defaultdict(list)
    for item in snapshot.territories:
        by_city[item.city_id].append(item)
    for rows in by_city.values():
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if years_overlap(left.start_year, left.end_year, right.start_year, right.end_year):
                    _issue(
                        report,
                        rule="city_ownership",
                        message=(
                            f"{left.city_name} 在 {left.faction_name} 与 {right.faction_name} 的归属时段重叠"
                        ),
                        entity_type="faction_territory",
                        entity_id=left.id,
                        field="start_year",
                    )
        city = next((item for item in snapshot.cities if item.id == rows[0].city_id), None)
        faction_by_id = {item.id: item for item in snapshot.factions}
        for row in rows:
            if city is not None:
                if _outside(row.start_year, row.end_year, city.founded_year, city.destroyed_year):
                    _issue(
                        report,
                        rule="territory_timeline",
                        message=f"{row.city_name} 的归属时段超出城池存续年",
                        entity_type="faction_territory",
                        entity_id=row.id,
                        field="start_year",
                    )
            faction = faction_by_id.get(row.faction_id)
            if faction is not None and _outside(row.start_year, row.end_year, faction.start_year, faction.end_year):
                _issue(
                    report,
                    rule="territory_timeline",
                    message=f"{row.city_name} 的归属时段超出 {faction.name} 存续年",
                    entity_type="faction_territory",
                    entity_id=row.id,
                    field="start_year",
                )


def _check_members(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    by_character: dict[str, list] = defaultdict(list)
    for item in snapshot.members:
        by_character[item.character_id].append(item)
        for year in (item.start_year, item.end_year):
            if year is None:
                continue
            try:
                validate_character_alive_in_year(
                    character_name=item.character_name,
                    birth_year=item.birth_year,
                    death_year=item.death_year,
                    event_year=year,
                )
            except ValidationError as exc:
                _from_validation_error(
                    report, exc, rule="member_timeline", entity_type="faction_member", entity_id=item.id
                )
                break
    for rows in by_character.values():
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if left.faction_id == right.faction_id:
                    continue
                if years_overlap(left.start_year, left.end_year, right.start_year, right.end_year):
                    _issue(
                        report,
                        rule="member_overlap",
                        message=(
                            f"{left.character_name} 同时属于 {left.faction_name} 与 {right.faction_name}"
                        ),
                        entity_type="faction_member",
                        entity_id=left.id,
                        field="start_year",
                    )


def _check_relationships(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    for item in snapshot.relationships:
        try:
            validate_relationship_years(item.start_year, item.end_year)
            validate_years_against_lifespan(
                from_birth=item.from_birth,
                from_death=item.from_death,
                to_birth=item.to_birth,
                to_death=item.to_death,
                start_year=item.start_year,
                end_year=item.end_year,
            )
        except ValidationError as exc:
            _from_validation_error(
                report, exc, rule="relationship_timeline", entity_type="relationship", entity_id=item.id
            )


def _check_stories(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    for story in snapshot.stories:
        graph = analyze_story_graph(list(story.nodes), list(story.edges))
        rule = "story_cycle" if graph.has_unconditional_cycle else "story_graph"
        for message in graph.errors:
            _issue(
                report,
                rule=rule,
                message=f"{story.name}：{message}",
                entity_type="story",
                entity_id=story.id,
            )


def _check_resources(snapshot: ProjectSnapshot, report: ValidationReport) -> None:
    for item in snapshot.resources:
        if not item.exists:
            _issue(
                report,
                rule="resource_path",
                message=f"{item.name} 的文件不存在：{item.path}",
                entity_type="resource",
                entity_id=item.id,
                field="path",
            )
        elif not item.checksum_ok:
            _issue(
                report,
                rule="resource_checksum",
                message=f"{item.name} 的 checksum 与文件内容不一致",
                entity_type="resource",
                entity_id=item.id,
                field="checksum",
            )


def _outside(
    inner_start: int | None,
    inner_end: int | None,
    outer_start: int | None,
    outer_end: int | None,
) -> bool:
    if outer_start is not None and inner_end is not None and inner_end < outer_start:
        return True
    if outer_end is not None and inner_start is not None and inner_start > outer_end:
        return True
    if outer_start is not None and inner_start is not None and inner_start < outer_start:
        return True
    if outer_end is not None and inner_end is not None and inner_end > outer_end:
        return True
    return False
