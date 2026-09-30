from typing import Any, Generic, TypeVar
from sqlalchemy import select, func, Select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: str) -> ModelType | None:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_by_id_and_user(self, id: str, user_id: str) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id, self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, obj: ModelType) -> ModelType:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.commit()
    
    async def paginate(self, query: Select, page: int = 1, page_size: int = 20) -> tuple[list[ModelType], int]:
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Get items
        offset = (page - 1) * page_size
        result = await self.session.execute(query.offset(offset).limit(page_size))
        items = list(result.scalars().all())
        
        return items, total
