from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_event import TaskEvent
from app.repositories.base import BaseRepository


class TaskEventRepository(BaseRepository[TaskEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(TaskEvent, session)

    async def list_by_task(
        self, task_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[TaskEvent], int]:
        query = (
            select(self.model)
            .where(self.model.task_id == task_id)
            .order_by(desc(self.model.created_at))
        )
        return await self.paginate(query, page, page_size)
