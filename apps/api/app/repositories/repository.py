from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.repositories.base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    def __init__(self, session: AsyncSession):
        super().__init__(Repository, session)

    async def create(self, data: dict) -> Repository:
        repo = Repository(**data)
        self.session.add(repo)
        await self.session.commit()
        await self.session.refresh(repo)
        return repo

    async def update(self, repo: Repository, data: dict) -> Repository:
        for key, value in data.items():
            setattr(repo, key, value)
        await self.session.commit()
        await self.session.refresh(repo)
        return repo

    async def delete(self, id_or_obj) -> None:
        if isinstance(id_or_obj, str):
            obj = await self.get_by_id(id_or_obj)
            if obj:
                await self.session.delete(obj)
                await self.session.commit()
        else:
            await self.session.delete(id_or_obj)
            await self.session.commit()

    async def list_by_project(self, project_id: str) -> list[Repository]:
        result = await self.session.execute(
            select(self.model).where(self.model.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: str) -> Repository | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
