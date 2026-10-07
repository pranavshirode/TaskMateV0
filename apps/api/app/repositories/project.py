import uuid
from typing import Optional, List
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20, client_id: Optional[uuid.UUID] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        if client_id:
            stmt = stmt.where(Project.client_id == client_id)
        if status:
            stmt = stmt.where(Project.status == status)
        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(desc(Project.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, user_id: uuid.UUID, client_id: Optional[uuid.UUID] = None, status: Optional[str] = None, search: Optional[str] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Project.id)).where(Project.user_id == user_id)
        if client_id:
            stmt = stmt.where(Project.client_id == client_id)
        if status:
            stmt = stmt.where(Project.status == status)
        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, user_id: uuid.UUID, obj_in: ProjectCreate) -> Project:
        db_obj = Project(**obj_in.model_dump(), user_id=user_id)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Project, obj_in: ProjectUpdate) -> Project:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def archive(self, db_obj: Project) -> Project:
        from datetime import datetime, timezone
        db_obj.status = "ARCHIVED"
        db_obj.archived_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
