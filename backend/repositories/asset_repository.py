"""资源仓储。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.asset import Resource


class AssetRepository:
    """资源持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, resource: Resource) -> Resource:
        """插入资源。"""
        self._session.add(resource)
        await self._session.flush()
        return resource

    async def get(self, project_id: str, resource_id: str) -> Resource | None:
        """按 ID 加载资源及模型扩展。"""
        result = await self._session.execute(
            select(Resource)
            .options(selectinload(Resource.model_asset))
            .where(Resource.project_id == project_id, Resource.id == resource_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> Resource | None:
        """按业务 code 查询。"""
        result = await self._session.execute(
            select(Resource).where(Resource.project_id == project_id, Resource.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[Resource]:
        """列出项目全部资源。"""
        result = await self._session.execute(
            select(Resource)
            .options(selectinload(Resource.model_asset))
            .where(Resource.project_id == project_id)
            .order_by(Resource.resource_type, Resource.code)
        )
        return list(result.scalars().all())

    async def delete(self, resource: Resource) -> None:
        """删除资源登记。"""
        await self._session.delete(resource)
        await self._session.flush()
