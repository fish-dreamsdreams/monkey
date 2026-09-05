"""史料目录与引文仓储。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.event import EventSource
from backend.models.source import CharacterSource, Source


class SourceRepository:
    """来源目录与人物引文持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, sources: list[Source]) -> None:
        """批量插入来源。"""
        self._session.add_all(sources)
        await self._session.flush()

    async def add(self, source: Source) -> Source:
        """插入单条来源。"""
        self._session.add(source)
        await self._session.flush()
        return source

    async def list_by_project(self, project_id: str) -> list[Source]:
        """列出项目来源目录。"""
        result = await self._session.execute(
            select(Source).where(Source.project_id == project_id).order_by(Source.source_type, Source.code)
        )
        return list(result.scalars().all())

    async def get(self, project_id: str, source_id: str) -> Source | None:
        """按 ID 获取来源。"""
        result = await self._session.execute(
            select(Source).where(Source.project_id == project_id, Source.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Source | None:
        """按业务 code 获取来源。"""
        result = await self._session.execute(
            select(Source).where(Source.project_id == project_id, Source.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_codes(self, project_id: str, codes: list[str]) -> list[Source]:
        """按一组 code 加载来源。"""
        if not codes:
            return []
        result = await self._session.execute(
            select(Source).where(Source.project_id == project_id, Source.code.in_(codes))
        )
        return list(result.scalars().all())

    async def count_usages(self, source_id: str) -> int:
        """统计人物引文与事件引文数量。"""
        character_count = await self._session.scalar(
            select(func.count()).select_from(CharacterSource).where(CharacterSource.source_id == source_id)
        )
        event_count = await self._session.scalar(
            select(func.count()).select_from(EventSource).where(EventSource.source_id == source_id)
        )
        return int(character_count or 0) + int(event_count or 0)

    async def delete(self, source: Source) -> None:
        """删除来源目录条目。"""
        await self._session.delete(source)
        await self._session.flush()

    async def add_citation(self, citation: CharacterSource) -> CharacterSource:
        """插入人物引文。"""
        self._session.add(citation)
        await self._session.flush()
        loaded = await self._session.execute(
            select(CharacterSource)
            .options(selectinload(CharacterSource.source))
            .where(CharacterSource.id == citation.id)
        )
        return loaded.scalar_one()

    async def get_citation(self, character_id: str, citation_id: str) -> CharacterSource | None:
        """获取人物的一条引文。"""
        result = await self._session.execute(
            select(CharacterSource)
            .options(selectinload(CharacterSource.source))
            .where(CharacterSource.character_id == character_id, CharacterSource.id == citation_id)
        )
        return result.scalar_one_or_none()

    async def delete_citation(self, citation: CharacterSource) -> None:
        """删除引文。"""
        await self._session.delete(citation)
        await self._session.flush()
