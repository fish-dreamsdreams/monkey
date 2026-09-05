"""API 路由汇总。"""

from fastapi import APIRouter

from backend.api.characters import router as characters_router
from backend.api.meta import router as meta_router
from backend.api.projects import router as projects_router
from backend.api.sources import router as sources_router

api_router = APIRouter()
api_router.include_router(meta_router)
api_router.include_router(projects_router)
api_router.include_router(sources_router)
api_router.include_router(characters_router)
