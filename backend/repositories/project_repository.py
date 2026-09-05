"""项目仓储。

职责：项目与性格标签的数据库读写，不包含 HTTP 语义。
"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.clock import utc_now

from backend.models.character import Character
from backend.models.event import EventSource, HistoricalEvent
from backend.models.personality import PersonalityTag
from backend.models.project import Project
from backend.models.source import CharacterSource


class ProjectRepository:
    """项目持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> Project:
        """插入项目。"""
        self._session.add(project)
        await self._session.flush()
        return project

    async def get(self, project_id: str) -> Project | None:
        """按 ID 查询项目。"""
        return await self._session.get(Project, project_id)

    async def get_by_code(self, code: str) -> Project | None:
        """按业务 code 查询项目。"""
        result = await self._session.execute(select(Project).where(Project.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Project]:
        """列出全部项目。"""
        result = await self._session.execute(select(Project).order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    async def add_tags(self, tags: list[PersonalityTag]) -> None:
        """批量写入性格标签。"""
        self._session.add_all(tags)
        await self._session.flush()

    async def list_tags(self, project_id: str) -> list[PersonalityTag]:
        """列出项目性格标签。"""
        result = await self._session.execute(
            select(PersonalityTag)
            .where(PersonalityTag.project_id == project_id)
            .order_by(PersonalityTag.is_system.desc(), PersonalityTag.code)
        )
        return list(result.scalars().all())

    async def get_tag(self, project_id: str, tag_id: str) -> PersonalityTag | None:
        """按 ID 查询性格标签。"""
        result = await self._session.execute(
            select(PersonalityTag).where(PersonalityTag.project_id == project_id, PersonalityTag.id == tag_id)
        )
        return result.scalar_one_or_none()

    async def delete_tag(self, tag: PersonalityTag) -> None:
        """删除性格标签。绑定记录随外键级联删除。"""
        await self._session.delete(tag)
        await self._session.flush()

    async def delete_project(self, project: Project) -> None:
        """删除项目。先清掉 RESTRICT 引文，再靠外键 CASCADE 清其余表。"""
        character_ids = select(Character.id).where(Character.project_id == project.id)
        await self._session.execute(delete(CharacterSource).where(CharacterSource.character_id.in_(character_ids)))
        event_ids = select(HistoricalEvent.id).where(HistoricalEvent.project_id == project.id)
        await self._session.execute(delete(EventSource).where(EventSource.event_id.in_(event_ids)))
        await self._session.execute(delete(Project).where(Project.id == project.id))
        await self._session.flush()

    async def get_tag_by_code(self, project_id: str, code: str) -> PersonalityTag | None:
        """按 code 查询性格标签。"""
        result = await self._session.execute(
            select(PersonalityTag).where(
                PersonalityTag.project_id == project_id,
                PersonalityTag.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def get_tags_by_codes(self, project_id: str, codes: list[str]) -> list[PersonalityTag]:
        """按一组 code 查询性格标签。"""
        if not codes:
            return []
        result = await self._session.execute(
            select(PersonalityTag).where(
                PersonalityTag.project_id == project_id,
                PersonalityTag.code.in_(codes),
            )
        )
        return list(result.scalars().all())

    async def bump_content_version(self, project: Project) -> None:
        """内容变更后递增项目内容版本。"""
        project.content_version += 1
        project.updated_at = utc_now()
        await self._session.flush()
