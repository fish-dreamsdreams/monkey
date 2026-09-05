"""城池仓储。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.city import City


class CityRepository:
    """城池持久化。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, city: City) -> City:
        """插入城池。"""
        self._session.add(city)
        await self._session.flush()
        return city

    async def get(self, project_id: str, city_id: str) -> City | None:
        """按 ID 加载城池。"""
        result = await self._session.execute(
            select(City).where(City.project_id == project_id, City.id == city_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_id: str, code: str) -> City | None:
        """按业务 code 加载城池。"""
        result = await self._session.execute(
            select(City).where(City.project_id == project_id, City.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[City]:
        """列出项目城池。"""
        result = await self._session.execute(
            select(City).where(City.project_id == project_id).order_by(City.name, City.code)
        )
        return list(result.scalars().all())

    async def delete(self, city: City) -> None:
        """删除城池。"""
        await self._session.delete(city)
        await self._session.flush()
