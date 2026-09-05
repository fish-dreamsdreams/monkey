"""FastAPI 依赖。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.repositories.asset_repository import AssetRepository
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.city_repository import CityRepository
from backend.repositories.event_repository import EventRepository
from backend.repositories.faction_repository import FactionRepository
from backend.repositories.map_repository import MapRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.relationship_repository import RelationshipRepository
from backend.repositories.skill_repository import SkillRepository
from backend.repositories.source_repository import SourceRepository
from backend.repositories.story_repository import StoryRepository
from backend.services.asset_service import AssetService
from backend.services.validation_service import ValidationService
from backend.services.character_service import CharacterService
from backend.services.city_service import CityService
from backend.services.event_service import EventService
from backend.services.faction_service import FactionService
from backend.services.map_service import MapService
from backend.services.project_service import ProjectService
from backend.services.relationship_service import RelationshipService
from backend.services.skill_service import SkillService
from backend.services.source_service import SourceService
from backend.services.export_service import ExportService
from backend.services.story_service import StoryService


def get_project_service(session: AsyncSession = Depends(get_db)) -> ProjectService:
    """构造项目服务。"""
    return ProjectService(ProjectRepository(session), SourceRepository(session))


def get_character_service(session: AsyncSession = Depends(get_db)) -> CharacterService:
    """构造人物服务。"""
    return CharacterService(
        CharacterRepository(session),
        ProjectRepository(session),
        SourceRepository(session),
    )


def get_source_service(session: AsyncSession = Depends(get_db)) -> SourceService:
    """构造史料目录服务。"""
    return SourceService(SourceRepository(session), ProjectRepository(session))


def get_relationship_service(session: AsyncSession = Depends(get_db)) -> RelationshipService:
    """构造人物关系服务。"""
    return RelationshipService(
        RelationshipRepository(session),
        CharacterRepository(session),
        ProjectRepository(session),
    )


def get_skill_service(session: AsyncSession = Depends(get_db)) -> SkillService:
    """构造技能服务。"""
    return SkillService(
        SkillRepository(session),
        CharacterRepository(session),
        ProjectRepository(session),
        SourceRepository(session),
    )


def get_city_service(session: AsyncSession = Depends(get_db)) -> CityService:
    """构造城池服务。"""
    return CityService(
        CityRepository(session),
        FactionRepository(session),
        ProjectRepository(session),
    )


def get_faction_service(session: AsyncSession = Depends(get_db)) -> FactionService:
    """构造势力服务。"""
    city_repo = CityRepository(session)
    faction_repo = FactionRepository(session)
    projects = ProjectRepository(session)
    return FactionService(
        faction_repo,
        city_repo,
        CharacterRepository(session),
        projects,
        CityService(city_repo, faction_repo, projects),
    )


def get_map_service(session: AsyncSession = Depends(get_db)) -> MapService:
    """构造地图服务。"""
    return MapService(
        MapRepository(session),
        CityRepository(session),
        ProjectRepository(session),
    )


def get_event_service(session: AsyncSession = Depends(get_db)) -> EventService:
    """构造历史事件服务。"""
    return EventService(
        EventRepository(session),
        CharacterRepository(session),
        CityRepository(session),
        FactionRepository(session),
        SourceRepository(session),
        ProjectRepository(session),
    )


def get_validation_service(session: AsyncSession = Depends(get_db)) -> ValidationService:
    """构造只读校验服务。"""
    return ValidationService(
        CharacterRepository(session),
        CityRepository(session),
        FactionRepository(session),
        EventRepository(session),
        RelationshipRepository(session),
        StoryRepository(session),
        AssetRepository(session),
        ProjectRepository(session),
    )


def get_asset_service(session: AsyncSession = Depends(get_db)) -> AssetService:
    """构造资源服务。"""
    return AssetService(
        AssetRepository(session),
        CharacterRepository(session),
        SkillRepository(session),
        CityRepository(session),
        MapRepository(session),
        ProjectRepository(session),
    )


def get_story_service(session: AsyncSession = Depends(get_db)) -> StoryService:
    """构造剧情服务。"""
    return StoryService(
        StoryRepository(session),
        CharacterRepository(session),
        CityRepository(session),
        FactionRepository(session),
        EventRepository(session),
        ProjectRepository(session),
    )


def get_export_service(
    projects: ProjectService = Depends(get_project_service),
    sources: SourceService = Depends(get_source_service),
    characters: CharacterService = Depends(get_character_service),
    relationships: RelationshipService = Depends(get_relationship_service),
    skills: SkillService = Depends(get_skill_service),
    cities: CityService = Depends(get_city_service),
    factions: FactionService = Depends(get_faction_service),
    maps: MapService = Depends(get_map_service),
    events: EventService = Depends(get_event_service),
    stories: StoryService = Depends(get_story_service),
    assets: AssetService = Depends(get_asset_service),
    validation: ValidationService = Depends(get_validation_service),
) -> ExportService:
    """构造导入导出服务。"""
    return ExportService(
        projects,
        sources,
        characters,
        relationships,
        skills,
        cities,
        factions,
        maps,
        events,
        stories,
        assets,
        validation,
    )
