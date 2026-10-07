import uuid
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryUpdate

class CodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, repository_id: uuid.UUID) -> Optional[Repository]:
        stmt = select(Repository).where(Repository.id == repository_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> List[Repository]:
        stmt = select(Repository).where(Repository.project_id == project_id).order_by(desc(Repository.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: RepositoryCreate) -> Repository:
        db_obj = Repository(**obj_in.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Repository, obj_in: RepositoryUpdate) -> Repository:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Repository) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
