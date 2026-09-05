"""人物应用服务。

职责：编排人物的创建、查询、更新与删除；协调领域校验与仓储。
不包含战斗、AI、动画等游戏运行逻辑。
"""

from backend.core.clock import utc_now
from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.core.ids import EntityPrefix, new_id
from backend.domain.character_rules import validate_lifespan
from backend.domain.source_types import BoundLayer, SourceType, is_fact_eligible, validate_citation_layer
from backend.models.character import Character, CharacterAttribute, CharacterHistoricalRecord
from backend.models.personality import CharacterPersonality, PersonalityTag
from backend.models.source import CharacterSource, Source
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.source_repository import SourceRepository
from backend.schemas.character import (
    CharacterBaseInfo,
    CharacterCreate,
    CharacterGameData,
    CharacterHistoricalData,
    CharacterPersonalityRead,
    CharacterRead,
    CharacterSummary,
    CharacterUpdate,
    Gender,
)
from backend.schemas.source import CharacterSourceRead, CharacterSourceWrite


class CharacterService:
    """人物用例编排。"""

    def __init__(
        self,
        characters: CharacterRepository,
        projects: ProjectRepository,
        sources: SourceRepository,
    ) -> None:
        self._characters = characters
        self._projects = projects
        self._sources = sources

    async def create(self, project_id: str, payload: CharacterCreate) -> CharacterRead:
        """创建人物，分别写入历史事实与游戏设定。"""
        await self._require_project(project_id)
        validate_lifespan(payload.base.birth_year, payload.base.death_year)
        if await self._characters.get_by_code(project_id, payload.base.code) is not None:
            raise ConflictError(f"人物 code 已存在: {payload.base.code}")

        tags = await self._resolve_tags(project_id, payload.game.personality_tag_codes)
        now = utc_now()
        character = Character(
            id=new_id(EntityPrefix.CHARACTER),
            project_id=project_id,
            code=payload.base.code,
            name=payload.base.name.strip(),
            courtesy_name=payload.base.courtesy_name,
            gender=payload.base.gender.value,
            birth_year=payload.base.birth_year,
            death_year=payload.base.death_year,
            birthplace=payload.base.birthplace,
            ethnicity=payload.base.ethnicity,
            identity=payload.base.identity,
            created_at=now,
            updated_at=now,
        )
        character.historical_record = self._build_historical(character.id, payload.historical)
        character.attributes = [self._build_attributes(character.id, payload.game)]
        character.personalities = [
            CharacterPersonality(character_id=character.id, personality_tag_id=tag.id, intensity=3)
            for tag in tags
        ]
        character.citations = await self._build_citations(project_id, character.id, payload.sources)
        await self._characters.add(character)
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
        created = await self._characters.get(project_id, character.id)
        if created is None:
            raise NotFoundError("人物创建后读取失败")
        return self._to_read(created)

    async def get(self, project_id: str, character_id: str) -> CharacterRead:
        """获取人物详情。"""
        await self._require_project(project_id)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        return self._to_read(character)

    async def list_characters(
        self,
        project_id: str,
        skip: int,
        limit: int,
    ) -> tuple[list[CharacterSummary], int]:
        """分页列出人物摘要。"""
        await self._require_project(project_id)
        items, total = await self._characters.list_by_project(project_id, skip, limit)
        summaries = [
            CharacterSummary(
                id=item.id,
                code=item.code,
                name=item.name,
                courtesy_name=item.courtesy_name,
                gender=Gender(item.gender),
                birth_year=item.birth_year,
                death_year=item.death_year,
                identity=item.identity,
            )
            for item in items
        ]
        return summaries, total

    async def update(self, project_id: str, character_id: str, payload: CharacterUpdate) -> CharacterRead:
        """全量更新人物。游戏数值不会写入历史表。"""
        await self._require_project(project_id)
        validate_lifespan(payload.base.birth_year, payload.base.death_year)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")

        duplicate = await self._characters.get_by_code(project_id, payload.base.code)
        if duplicate is not None and duplicate.id != character.id:
            raise ConflictError(f"人物 code 已存在: {payload.base.code}")

        tags = await self._resolve_tags(project_id, payload.game.personality_tag_codes)
        character.code = payload.base.code
        character.name = payload.base.name.strip()
        character.courtesy_name = payload.base.courtesy_name
        character.gender = payload.base.gender.value
        character.birth_year = payload.base.birth_year
        character.death_year = payload.base.death_year
        character.birthplace = payload.base.birthplace
        character.ethnicity = payload.base.ethnicity
        character.identity = payload.base.identity
        character.updated_at = utc_now()

        if character.historical_record is None:
            character.historical_record = self._build_historical(character.id, payload.historical)
        else:
            self._apply_historical(character.historical_record, payload.historical)

        default_attr = next((item for item in character.attributes if item.version_name == payload.game.attribute_version), None)
        if default_attr is None:
            character.attributes.append(self._build_attributes(character.id, payload.game))
        else:
            self._apply_attributes(default_attr, payload.game)

        character.personalities.clear()
        await self._characters.flush()
        character.personalities = [
            CharacterPersonality(character_id=character.id, personality_tag_id=tag.id, intensity=3)
            for tag in tags
        ]
        if payload.sources is not None:
            character.citations.clear()
            await self._characters.flush()
            character.citations = await self._build_citations(project_id, character.id, payload.sources)

        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)

        updated = await self._characters.get(project_id, character.id)
        if updated is None:
            raise NotFoundError("人物更新后读取失败")
        return self._to_read(updated)

    async def delete(self, project_id: str, character_id: str) -> None:
        """删除人物。"""
        await self._require_project(project_id)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        await self._characters.delete(character)
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)

    async def _require_project(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")

    async def add_citation(
        self,
        project_id: str,
        character_id: str,
        payload: CharacterSourceWrite,
    ) -> CharacterSourceRead:
        """为已有人物追加一条引文。"""
        character = await self._require_character(project_id, character_id)
        citations = await self._build_citations(project_id, character.id, [payload])
        saved = await self._sources.add_citation(citations[0])
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
        return self._to_citation_read(saved)

    async def delete_citation(self, project_id: str, character_id: str, citation_id: str) -> None:
        """删除人物引文。"""
        await self._require_character(project_id, character_id)
        citation = await self._sources.get_citation(character_id, citation_id)
        if citation is None:
            raise NotFoundError("引文不存在")
        await self._sources.delete_citation(citation)
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)

    async def _require_character(self, project_id: str, character_id: str) -> Character:
        await self._require_project(project_id)
        character = await self._characters.get(project_id, character_id)
        if character is None:
            raise NotFoundError("人物不存在")
        return character

    async def _build_citations(
        self,
        project_id: str,
        character_id: str,
        items: list[CharacterSourceWrite],
    ) -> list[CharacterSource]:
        catalog = await self._resolve_sources(project_id, [item.source_code for item in items])
        citations: list[CharacterSource] = []
        for item in items:
            source = catalog[item.source_code]
            source_type = SourceType(source.source_type)
            validate_citation_layer(source_type, item.bound_layer)
            citations.append(
                CharacterSource(
                    id=new_id(EntityPrefix.CITATION),
                    character_id=character_id,
                    source_id=source.id,
                    bound_layer=item.bound_layer.value,
                    quotation=item.quotation,
                    reference=item.reference,
                    note=item.note,
                    source=source,
                )
            )
        return citations

    async def _resolve_sources(self, project_id: str, codes: list[str]) -> dict[str, Source]:
        unique_codes = list(dict.fromkeys(codes))
        sources = await self._sources.get_by_codes(project_id, unique_codes)
        found = {item.code: item for item in sources}
        missing = [code for code in unique_codes if code not in found]
        if missing:
            raise ValidationError(f"来源不存在: {', '.join(missing)}", field="source_code")
        return found

    def _to_citation_read(self, citation: CharacterSource) -> CharacterSourceRead:
        source = citation.source
        source_type = SourceType(source.source_type)
        return CharacterSourceRead(
            id=citation.id,
            source_id=source.id,
            source_code=source.code,
            source_name=source.name,
            source_type=source_type,
            bound_layer=BoundLayer(citation.bound_layer),
            quotation=citation.quotation,
            reference=citation.reference,
            note=citation.note,
            fact_eligible=is_fact_eligible(source_type),
        )

    async def _resolve_tags(self, project_id: str, codes: list[str]) -> list[PersonalityTag]:
        unique_codes = list(dict.fromkeys(codes))
        tags = await self._projects.get_tags_by_codes(project_id, unique_codes)
        found = {tag.code for tag in tags}
        missing = [code for code in unique_codes if code not in found]
        if missing:
            raise ValidationError(f"性格标签不存在: {', '.join(missing)}", field="personality_tag_codes")
        return tags

    def _build_historical(self, character_id: str, data: CharacterHistoricalData) -> CharacterHistoricalRecord:
        record = CharacterHistoricalRecord(id=new_id(EntityPrefix.HISTORICAL_RECORD), character_id=character_id)
        self._apply_historical(record, data)
        return record

    def _apply_historical(self, record: CharacterHistoricalRecord, data: CharacterHistoricalData) -> None:
        record.biography = data.biography
        record.family_background = data.family_background
        record.life_experience = data.life_experience
        record.achievements = data.achievements
        record.historical_evaluation = data.historical_evaluation

    def _build_attributes(self, character_id: str, data: CharacterGameData) -> CharacterAttribute:
        attr = CharacterAttribute(
            id=new_id(EntityPrefix.ATTRIBUTE),
            character_id=character_id,
            version_name=data.attribute_version,
        )
        self._apply_attributes(attr, data)
        return attr

    def _apply_attributes(self, attr: CharacterAttribute, data: CharacterGameData) -> None:
        attr.force = data.force
        attr.intelligence = data.intelligence
        attr.politics = data.politics
        attr.charisma = data.charisma
        attr.leadership = data.leadership
        attr.stamina = data.stamina
        attr.morale = data.morale
        attr.mobility = data.mobility

    def _to_read(self, character: Character) -> CharacterRead:
        historical = character.historical_record
        attr = next(iter(character.attributes), None)
        personalities = [
            CharacterPersonalityRead(
                id=binding.tag.id,
                code=binding.tag.code,
                name=binding.tag.name,
                description=binding.tag.description,
                is_system=binding.tag.is_system,
                intensity=binding.intensity,
            )
            for binding in character.personalities
            if binding.tag is not None
        ]
        citations = [
            self._to_citation_read(item) for item in character.citations if item.source is not None
        ]
        return CharacterRead(
            id=character.id,
            project_id=character.project_id,
            base=CharacterBaseInfo(
                code=character.code,
                name=character.name,
                courtesy_name=character.courtesy_name,
                gender=Gender(character.gender),
                birth_year=character.birth_year,
                death_year=character.death_year,
                birthplace=character.birthplace,
                ethnicity=character.ethnicity,
                identity=character.identity,
            ),
            historical=CharacterHistoricalData(
                biography=historical.biography if historical else None,
                family_background=historical.family_background if historical else None,
                life_experience=historical.life_experience if historical else None,
                achievements=historical.achievements if historical else None,
                historical_evaluation=historical.historical_evaluation if historical else None,
            ),
            game=CharacterGameData(
                force=attr.force if attr else 50,
                intelligence=attr.intelligence if attr else 50,
                politics=attr.politics if attr else 50,
                charisma=attr.charisma if attr else 50,
                leadership=attr.leadership if attr else 50,
                stamina=attr.stamina if attr else 50,
                morale=attr.morale if attr else 50,
                mobility=attr.mobility if attr else 50,
                personality_tag_codes=[item.code for item in personalities],
                attribute_version=attr.version_name if attr else "default",
            ),
            personalities=personalities,
            sources=citations,
            created_at=character.created_at,
            updated_at=character.updated_at,
        )
