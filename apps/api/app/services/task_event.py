from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.task_event import TaskEventRepository
from app.repositories.task import TaskRepository
from app.schemas.task_event import TaskEventResponse
from app.schemas.common import PaginatedResponse
from app.core.errors import NotFoundError, ValidationError
from app.models.enums import TaskEventType
from app.models.task_event import TaskEvent

class TaskEventService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_repo = TaskEventRepository(session)
        self.task_repo = TaskRepository(session)
        
    async def list_by_task(self, user_id: str, task_id: str, page: int = 1, page_size: int = 20) -> PaginatedResponse[TaskEventResponse]:
        task = await self.task_repo.get_by_id(task_id)
        if not task or str(task.user_id) != user_id:
            raise ValidationError("Task not found or does not belong to user")
            
        events, total = await self.event_repo.list_by_task(
            task_id=task_id, page=page, page_size=page_size
        )
        
        items = [TaskEventResponse.model_validate(e) for e in events]
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
        
    async def create_event(self, task_id: str, user_id: str, event_type: TaskEventType, 
                           old_value: str | None = None, new_value: str | None = None) -> TaskEvent:
        event = TaskEvent(
            task_id=task_id,
            user_id=user_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value
        )
        return await self.event_repo.create(event)

