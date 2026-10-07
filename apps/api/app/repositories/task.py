import uuid
from typing import Optional, List
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskEvent
from app.schemas.task import TaskCreate, TaskUpdate

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Task]:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20,
                   project_id: Optional[uuid.UUID] = None, client_id: Optional[uuid.UUID] = None,
                   status: Optional[str] = None, priority: Optional[str] = None,
                   search: Optional[str] = None) -> List[Task]:
        stmt = select(Task).where(Task.user_id == user_id)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if client_id:
            stmt = stmt.where(Task.client_id == client_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if search:
            stmt = stmt.where(Task.title.ilike(f"%{search}%"))

        stmt = stmt.order_by(desc(Task.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, user_id: uuid.UUID, project_id: Optional[uuid.UUID] = None,
                    client_id: Optional[uuid.UUID] = None, status: Optional[str] = None,
                    priority: Optional[str] = None, search: Optional[str] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Task.id)).where(Task.user_id == user_id)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if client_id:
            stmt = stmt.where(Task.client_id == client_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if search:
            stmt = stmt.where(Task.title.ilike(f"%{search}%"))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, user_id: uuid.UUID, obj_in: TaskCreate) -> Task:
        db_obj = Task(**obj_in.model_dump(), user_id=user_id)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)

        await self._create_event(db_obj, user_id, "TASK_CREATED")
        return db_obj

    async def update(self, db_obj: Task, user_id: uuid.UUID, obj_in: TaskUpdate) -> Task:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)

        await self._create_event(db_obj, user_id, "TASK_UPDATED")
        return db_obj

    async def change_status(self, db_obj: Task, user_id: uuid.UUID, new_status: str) -> Task:
        old_status = db_obj.status
        db_obj.status = new_status
        if new_status == "COMPLETED":
            from datetime import datetime, timezone
            db_obj.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_obj)

        await self._create_event(db_obj, user_id, "STATUS_CHANGED", old_status, new_status)
        return db_obj

    async def change_priority(self, db_obj: Task, user_id: uuid.UUID, new_priority: str) -> Task:
        old_priority = db_obj.priority
        db_obj.priority = new_priority
        await self.session.commit()
        await self.session.refresh(db_obj)

        await self._create_event(db_obj, user_id, "PRIORITY_CHANGED", old_priority, new_priority)
        return db_obj

    async def archive(self, db_obj: Task, user_id: uuid.UUID) -> Task:
        from datetime import datetime, timezone
        db_obj.archived_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_obj)

        await self._create_event(db_obj, user_id, "TASK_ARCHIVED")
        return db_obj

    async def get_events(self, task_id: uuid.UUID, user_id: uuid.UUID) -> List[TaskEvent]:
        stmt = select(TaskEvent).where(TaskEvent.task_id == task_id, TaskEvent.user_id == user_id).order_by(desc(TaskEvent.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _create_event(self, task: Task, user_id: uuid.UUID, event_type: str, old_val: Optional[str] = None, new_val: Optional[str] = None):
        event = TaskEvent(
            task_id=task.id,
            user_id=user_id,
            event_type=event_type,
            old_value=old_val,
            new_value=new_val
        )
        self.session.add(event)
        await self.session.commit()
