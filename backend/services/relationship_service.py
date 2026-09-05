"""人物关系应用服务。

职责：创建/更新/删除关系，维护对称双向边，并做时段重叠校验。
不包含游戏运行时的好感度结算。
"""

from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_id, require_id
from backend.domain.relationship_types import (
    RelationshipType,
    is_symmetric,
    validate_not_self,
    validate_relationship_years,
    validate_years_against_lifespan,
    years_overlap,
)
from backend.models.character import Character
from backend.models.relationship import CharacterRelationship
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.relationship_repository import RelationshipRepository
from backend.schemas.relationship import (
    CharacterRef,
    CharacterRelationshipGraph,
    RelationshipCreate,
    RelationshipRead,
    RelationshipUpdate,
)


class RelationshipService:
    """人物关系用例编排。"""

    def __init__(
        self,
        relationships: RelationshipRepository,
        characters: CharacterRepository,
        projects: ProjectRepository,
    ) -> None:
        self._relationships = relationships
        self._characters = characters
        self._projects = projects

    async def create(self, project_id: str, payload: RelationshipCreate) -> RelationshipRead:
        """创建关系。对称类型同时写入反向边。"""
        await self._require_project(project_id)
        from_id = require_id(payload.from_character_id, EntityPrefix.CHARACTER, field="from_character_id")
        to_id = require_id(payload.to_character_id, EntityPrefix.CHARACTER, field="to_character_id")
        validate_not_self(from_id, to_id)
        validate_relationship_years(payload.start_year, payload.end_year)
        from_character = await self._require_character(project_id, from_id)
        to_character = await self._require_character(project_id, to_id)
        validate_years_against_lifespan(
            from_birth=from_character.birth_year,
            from_death=from_character.death_year,
            to_birth=to_character.birth_year,
            to_death=to_character.death_year,
            start_year=payload.start_year,
            end_year=payload.end_year,
        )
        await self._assert_no_overlap(
            project_id,
            from_id,
            to_id,
            payload.relationship_type,
            payload.start_year,
            payload.end_year,
        )
        primary_id = new_id(EntityPrefix.RELATIONSHIP)
        primary = self._build_row(
            relationship_id=primary_id,
            project_id=project_id,
            pair_id=primary_id,
            from_character_id=from_id,
            to_character_id=to_id,
            payload=payload,
            is_primary=True,
        )
        rows = [primary]
        if is_symmetric(payload.relationship_type):
            rows.append(
                self._build_row(
                    relationship_id=new_id(EntityPrefix.RELATIONSHIP),
                    project_id=project_id,
                    pair_id=primary_id,
                    from_character_id=to_id,
                    to_character_id=from_id,
                    payload=payload,
                    is_primary=False,
                )
            )
        await self._relationships.add_many(rows)
        await self._bump(project_id)
        created = await self._relationships.get(project_id, primary_id)
        if created is None:
            raise NotFoundError("关系创建后读取失败")
        return self._to_read(created)

    async def get(self, project_id: str, relationship_id: str) -> RelationshipRead:
        """获取单条关系。"""
        await self._require_project(project_id)
        row = await self._relationships.get(project_id, relationship_id)
        if row is None:
            raise NotFoundError("关系不存在")
        return self._to_read(row)

    async def list_relationships(
        self,
        project_id: str,
        character_id: str | None = None,
    ) -> list[RelationshipRead]:
        """列出项目关系（仅主边）。"""
        await self._require_project(project_id)
        if character_id is not None:
            require_id(character_id, EntityPrefix.CHARACTER, field="character_id")
            await self._require_character(project_id, character_id)
        rows = await self._relationships.list_primary(project_id, character_id)
        return [self._to_read(row) for row in rows]

    async def graph_for_character(self, project_id: str, character_id: str) -> CharacterRelationshipGraph:
        """人物邻接关系。对称关系只返回从该人物出发的边，不对称关系另附入边。"""
        await self._require_project(project_id)
        await self._require_character(project_id, character_id)
        rows = await self._relationships.list_for_character(project_id, character_id)
        edges: list[RelationshipRead] = []
        for row in rows:
            rel_type = RelationshipType(row.relationship_type)
            if row.from_character_id == character_id:
                edges.append(self._to_read(row, direction="outgoing"))
            elif row.to_character_id == character_id and not is_symmetric(rel_type):
                edges.append(self._to_read(row, direction="incoming"))
        return CharacterRelationshipGraph(character_id=character_id, edges=edges)

    async def update(
        self,
        project_id: str,
        relationship_id: str,
        payload: RelationshipUpdate,
    ) -> RelationshipRead:
        """更新一对关系的属性。两端人物不可改。"""
        await self._require_project(project_id)
        current = await self._relationships.get(project_id, relationship_id)
        if current is None:
            raise NotFoundError("关系不存在")
        validate_relationship_years(payload.start_year, payload.end_year)
        from_character = current.from_character
        to_character = current.to_character
        validate_years_against_lifespan(
            from_birth=from_character.birth_year,
            from_death=from_character.death_year,
            to_birth=to_character.birth_year,
            to_death=to_character.death_year,
            start_year=payload.start_year,
            end_year=payload.end_year,
        )
        await self._assert_no_overlap(
            project_id,
            current.from_character_id,
            current.to_character_id,
            payload.relationship_type,
            payload.start_year,
            payload.end_year,
            exclude_pair_id=current.pair_id,
        )
        pair = await self._relationships.list_pair(project_id, current.pair_id)
        if is_symmetric(payload.relationship_type) and len(pair) == 1:
            inverse = self._build_row(
                relationship_id=new_id(EntityPrefix.RELATIONSHIP),
                project_id=project_id,
                pair_id=current.pair_id,
                from_character_id=current.to_character_id,
                to_character_id=current.from_character_id,
                payload=payload,
                is_primary=False,
            )
            await self._relationships.add_many([inverse])
            pair = await self._relationships.list_pair(project_id, current.pair_id)
        keep_ids: set[str] = set()
        primary = next((row for row in pair if row.is_primary), pair[0])
        keep_ids.add(primary.id)
        self._apply_payload(primary, payload)
        if is_symmetric(payload.relationship_type):
            inverse = next((row for row in pair if row.id != primary.id), None)
            if inverse is not None:
                self._apply_payload(inverse, payload)
                keep_ids.add(inverse.id)
        elif len(pair) > 1:
            extras = [row for row in pair if row.id not in keep_ids]
            await self._relationships.delete_pair(extras)
        await self._bump(project_id)
        updated = await self._relationships.get(project_id, primary.id)
        if updated is None:
            raise NotFoundError("关系更新后读取失败")
        return self._to_read(updated)

    async def delete(self, project_id: str, relationship_id: str) -> None:
        """删除关系及其对称反向边。"""
        await self._require_project(project_id)
        current = await self._relationships.get(project_id, relationship_id)
        if current is None:
            raise NotFoundError("关系不存在")
        pair = await self._relationships.list_pair(project_id, current.pair_id)
        await self._relationships.delete_pair(pair)
        await self._bump(project_id)

    async def _assert_no_overlap(
        self,
        project_id: str,
        from_id: str,
        to_id: str,
        relationship_type: RelationshipType,
        start_year: int | None,
        end_year: int | None,
        exclude_pair_id: str | None = None,
    ) -> None:
        existing = await self._relationships.list_same_type_between(
            project_id,
            from_id,
            to_id,
            relationship_type.value,
        )
        seen_pairs: set[str] = set()
        for row in existing:
            if row.pair_id in seen_pairs:
                continue
            seen_pairs.add(row.pair_id)
            if exclude_pair_id is not None and row.pair_id == exclude_pair_id:
                continue
            if years_overlap(start_year, end_year, row.start_year, row.end_year):
                raise ConflictError("同一对人物在重叠时段已存在相同类型关系")

    def _build_row(
        self,
        *,
        relationship_id: str,
        project_id: str,
        pair_id: str,
        from_character_id: str,
        to_character_id: str,
        payload: RelationshipCreate | RelationshipUpdate,
        is_primary: bool,
    ) -> CharacterRelationship:
        return CharacterRelationship(
            id=relationship_id,
            project_id=project_id,
            pair_id=pair_id,
            from_character_id=from_character_id,
            to_character_id=to_character_id,
            relationship_type=payload.relationship_type.value,
            intimacy=payload.intimacy,
            hostility=payload.hostility,
            start_year=payload.start_year,
            end_year=payload.end_year,
            note=payload.note,
            is_primary=is_primary,
        )

    def _apply_payload(self, row: CharacterRelationship, payload: RelationshipUpdate) -> None:
        row.relationship_type = payload.relationship_type.value
        row.intimacy = payload.intimacy
        row.hostility = payload.hostility
        row.start_year = payload.start_year
        row.end_year = payload.end_year
        row.note = payload.note

    def _to_read(self, row: CharacterRelationship, direction: str | None = None) -> RelationshipRead:
        rel_type = RelationshipType(row.relationship_type)
        return RelationshipRead(
            id=row.id,
            project_id=row.project_id,
            pair_id=row.pair_id,
            from_character=CharacterRef(
                id=row.from_character.id,
                code=row.from_character.code,
                name=row.from_character.name,
            ),
            to_character=CharacterRef(
                id=row.to_character.id,
                code=row.to_character.code,
                name=row.to_character.name,
            ),
            relationship_type=rel_type,
            symmetric=is_symmetric(rel_type),
            intimacy=row.intimacy,
            hostility=row.hostility,
            start_year=row.start_year,
            end_year=row.end_year,
            note=row.note,
            is_primary=row.is_primary,
            direction=direction,
        )

    async def _require_character(self, project_id: str, character_id: str) -> Character:
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        return character

    async def _require_project(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")

    async def _bump(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
