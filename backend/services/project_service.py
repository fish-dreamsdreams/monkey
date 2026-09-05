"""项目应用服务。

职责：创建/更新内容项目、写入预置性格标签，并保证项目上下文字段稳定。
"""

from backend.core.clock import utc_now
from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.ids import EntityPrefix, new_business_code, new_id
from backend.core.schema_version import CURRENT_SCHEMA_VERSION
from backend.domain.character_rules import validate_historical_year_range
from backend.domain.personality import SYSTEM_PERSONALITY_TAGS
from backend.models.personality import PersonalityTag
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.personality import PersonalityTagCreate
from backend.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


class ProjectService:
    """项目用例编排。"""

    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def create(self, payload: ProjectCreate) -> ProjectRead:
        """创建项目并初始化系统性格标签。"""
        validate_historical_year_range(payload.target_start_year, payload.target_end_year)
        code = payload.code or new_business_code("proj")
        if await self._projects.get_by_code(code) is not None:
            raise ConflictError(f"项目 code 已存在: {code}")
        now = utc_now()
        project = Project(
            id=new_id(EntityPrefix.PROJECT),
            code=code,
            name=payload.name.strip(),
            description=payload.description,
            schema_version=CURRENT_SCHEMA_VERSION,
            content_version=1,
            target_start_year=payload.target_start_year,
            target_end_year=payload.target_end_year,
            created_at=now,
            updated_at=now,
        )
        await self._projects.add(project)
        tags = [
            PersonalityTag(
                id=new_id(EntityPrefix.PERSONALITY_TAG),
                project_id=project.id,
                code=tag_code,
                name=name,
                is_system=True,
            )
            for tag_code, name in SYSTEM_PERSONALITY_TAGS
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

    async def update(self, project_id: str, payload: ProjectUpdate) -> ProjectRead:
        """更新项目元数据。不修改 code 与 schema_version。"""
        validate_historical_year_range(payload.target_start_year, payload.target_end_year)
        project = await self._require_project(project_id)
        project.name = payload.name.strip()
        project.description = payload.description
        project.target_start_year = payload.target_start_year
        project.target_end_year = payload.target_end_year
        await self._projects.bump_content_version(project)
        return ProjectRead.model_validate(project)

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
            id=new_id(EntityPrefix.PERSONALITY_TAG),
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
