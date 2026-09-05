"""API 路由汇总。"""

from fastapi import APIRouter

from backend.api.assets import router as assets_router
from backend.api.characters import router as characters_router
from backend.api.cities import router as cities_router
from backend.api.events import router as events_router
from backend.api.factions import router as factions_router
from backend.api.maps import router as maps_router
from backend.api.meta import router as meta_router
from backend.api.projects import router as projects_router
from backend.api.relationships import router as relationships_router
from backend.api.skills import router as skills_router
from backend.api.sources import router as sources_router
from backend.api.stories import router as stories_router
from backend.api.validation import router as validation_router

api_router = APIRouter()
api_router.include_router(meta_router)
api_router.include_router(projects_router)
api_router.include_router(sources_router)
api_router.include_router(relationships_router)
api_router.include_router(skills_router)
api_router.include_router(cities_router)
api_router.include_router(factions_router)
api_router.include_router(maps_router)
api_router.include_router(events_router)
api_router.include_router(stories_router)
api_router.include_router(assets_router)
api_router.include_router(validation_router)
api_router.include_router(characters_router)
