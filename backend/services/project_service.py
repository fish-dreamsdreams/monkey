"""项目应用服务。

职责：创建内容项目并写入预置性格标签，提供最小项目上下文给人物模块。
"""

from backend.core.clock import utc_now
from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import new_id
from backend.domain.character_rules import validate_historical_year_range
from backend.domain.personality import SYSTEM_PERSONALITY_TAGS
from backend.models.personality import PersonalityTag
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.personality import PersonalityTagCreate
from backend.schemas.project import ProjectCreate, ProjectRead


class ProjectService:
    """项目用例编排。"""

    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def create(self, payload: ProjectCreate) -> ProjectRead:
        """创建项目并初始化系统性格标签。"""
        validate_historical_year_range(payload.target_start_year, payload.target_end_year)
        now = utc_now()
        project = Project(
            id=new_id(),
            name=payload.name.strip(),
            description=payload.description,
            schema_version="1.0.0",
            content_version=1,
            target_start_year=payload.target_start_year,
            target_end_year=payload.target_end_year,
            created_at=now,
            updated_at=now,
        )
        await self._projects.add(project)
        tags = [
            PersonalityTag(
                id=new_id(),
                project_id=project.id,
                code=code,
                name=name,
                is_system=True,
            )
            for code, name in SYSTEM_PERSONALITY_TAGS
        ]
        await self._projects.add_tags(tags)
        return ProjectRead.model_validate(project)

    async def get(self, project_id: str) -> ProjectRead:
        """获取项目详情。"""
        project = await self._require_project(project_id)
        return ProjectRead.model_validate(project)

    async def list_projects(self) -> list[ProjectRead]:
        """列出项目。"""
        projects = await self._projects.list_all()
        return [ProjectRead.model_validate(item) for item in projects]

    async def list_personality_tags(self, project_id: str) -> list[PersonalityTag]:
        """列出项目性格标签。"""
        await self._require_project(project_id)
        return await self._projects.list_tags(project_id)

    async def create_personality_tag(self, project_id: str, payload: PersonalityTagCreate) -> PersonalityTag:
        """新增自定义性格标签。"""
        await self._require_project(project_id)
        exists = await self._projects.get_tag_by_code(project_id, payload.code)
        if exists is not None:
            raise ConflictError(f"性格标签 code 已存在: {payload.code}")
        tag = PersonalityTag(
            id=new_id(),
            project_id=project_id,
            code=payload.code,
            name=payload.name.strip(),
            is_system=False,
        )
        await self._projects.add_tags([tag])
        return tag

    async def _require_project(self, project_id: str) -> Project:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError("项目不存在")
        return project
