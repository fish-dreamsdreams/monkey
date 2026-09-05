"""FastAPI 依赖。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.repositories.character_repository import CharacterRepository
from backend.repositories.project_repository import ProjectRepository
from backend.services.character_service import CharacterService
from backend.services.project_service import ProjectService


def get_project_service(session: AsyncSession = Depends(get_db)) -> ProjectService:
    """构造项目服务。"""
    return ProjectService(ProjectRepository(session))


def get_character_service(session: AsyncSession = Depends(get_db)) -> CharacterService:
    """构造人物服务。"""
    return CharacterService(CharacterRepository(session), ProjectRepository(session))
