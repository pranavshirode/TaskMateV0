import uuid
from typing import Optional, List
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate

class ClientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, client_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Client]:
        stmt = select(Client).where(Client.id == client_id, Client.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20, search: Optional[str] = None) -> List[Client]:
        stmt = select(Client).where(Client.user_id == user_id)
        if search:
            stmt = stmt.where(Client.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(desc(Client.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, user_id: uuid.UUID, search: Optional[str] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Client.id)).where(Client.user_id == user_id)
        if search:
            stmt = stmt.where(Client.name.ilike(f"%{search}%"))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, user_id: uuid.UUID, obj_in: ClientCreate) -> Client:
        db_obj = Client(**obj_in.model_dump(), user_id=user_id)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Client, obj_in: ClientUpdate) -> Client:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def archive(self, db_obj: Client) -> Client:
        from datetime import datetime, timezone
        db_obj.status = "ARCHIVED"
        db_obj.archived_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
