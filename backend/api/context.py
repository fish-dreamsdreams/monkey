"""项目上下文依赖。

职责：所有内容 API 进入业务前，先校验项目 ID 格式、项目存在性和 schema 兼容性。
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.core.exceptions import NotFoundError, UnsupportedSchemaError
from backend.core.ids import EntityPrefix, require_id
from backend.core.schema_version import SUPPORTED_SCHEMA_VERSIONS
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository


class ProjectContext:
    """当前请求对应的内容项目。"""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.id = project.id
        self.code = project.code
        self.schema_version = project.schema_version


def valid_project_id(project_id: str) -> str:
    """校验路径参数 project_id。"""
    return require_id(project_id, EntityPrefix.PROJECT, field="project_id")


def valid_character_id(character_id: str) -> str:
    """校验路径参数 character_id。"""
    return require_id(character_id, EntityPrefix.CHARACTER, field="character_id")


async def get_project_context(
    project_id: str = Depends(valid_project_id),
    session: AsyncSession = Depends(get_db),
) -> ProjectContext:
    """加载并校验当前项目上下文。"""
    project = await ProjectRepository(session).get(project_id)
    if project is None:
        raise NotFoundError("项目不存在")
    if project.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaError(
            f"项目 schema_version={project.schema_version} 不被当前编辑器支持"
        )
    return ProjectContext(project)
