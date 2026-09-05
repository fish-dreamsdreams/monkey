"""史料目录应用服务。"""

from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_id
from backend.domain.source_types import SourceType, is_fact_eligible, validate_source_definition
from backend.models.source import Source
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.source_repository import SourceRepository
from backend.schemas.source import SourceCreate, SourceRead


def to_source_read(source: Source) -> SourceRead:
    """把来源模型转成 API 读取结构。"""
    source_type = SourceType(source.source_type)
    return SourceRead(
        id=source.id,
        project_id=source.project_id,
        code=source.code,
        name=source.name,
        source_type=source_type,
        is_system=source.is_system,
        fact_eligible=is_fact_eligible(source_type),
    )


class SourceService:
    """项目来源目录用例。"""

    def __init__(self, sources: SourceRepository, projects: ProjectRepository) -> None:
        self._sources = sources
        self._projects = projects

    async def list_sources(self, project_id: str) -> list[SourceRead]:
        """列出项目来源。"""
        await self._require_project(project_id)
        items = await self._sources.list_by_project(project_id)
        return [to_source_read(item) for item in items]

    async def create(self, project_id: str, payload: SourceCreate) -> SourceRead:
        """新增自定义来源。"""
        await self._require_project(project_id)
        validate_source_definition(payload.name, payload.source_type)
        if await self._sources.get_by_code(project_id, payload.code) is not None:
            raise ConflictError(f"来源 code 已存在: {payload.code}")
        source = Source(
            id=new_id(EntityPrefix.SOURCE),
            project_id=project_id,
            code=payload.code,
            name=payload.name.strip(),
            source_type=payload.source_type.value,
            is_system=False,
        )
        await self._sources.add(source)
        project = await self._projects.get(project_id)
        if project is not None:
            await self._projects.bump_content_version(project)
        return to_source_read(source)

    async def _require_project(self, project_id: str) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
