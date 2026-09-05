"""FastAPI 依赖。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.relationship_repository import RelationshipRepository
from backend.repositories.source_repository import SourceRepository
from backend.services.character_service import CharacterService
from backend.services.project_service import ProjectService
from backend.services.relationship_service import RelationshipService
from backend.services.source_service import SourceService


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
