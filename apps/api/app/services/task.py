from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository
from app.repositories.client import ClientRepository
from app.repositories.task_event import TaskEventRepository
from app.repositories.task_label import TaskLabelRepository
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusUpdate, TaskPriorityUpdate
from app.schemas.common import PaginatedResponse
from app.core.errors import NotFoundError, ValidationError
from app.models.enums import TaskStatus, TaskPriority, TaskEventType
from app.models.task_event import TaskEvent
from app.models.task import Task

class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.project_repo = ProjectRepository(session)
        self.client_repo = ClientRepository(session)
        self.event_repo = TaskEventRepository(session)
        self.label_repo = TaskLabelRepository(session)
        
    async def _verify_project_ownership(self, user_id: str, project_id: str) -> None:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ValidationError("Invalid project_id or project does not belong to user")
            
    async def _verify_client_ownership(self, user_id: str, client_id: str) -> None:
        client = await self.client_repo.get_by_id(client_id)
        if not client or str(client.user_id) != user_id:
            raise ValidationError("Invalid client_id or client does not belong to user")
            
    async def create(self, user_id: str, data: TaskCreate) -> TaskResponse:
        if data.project_id:
            await self._verify_project_ownership(user_id, str(data.project_id))
        if data.client_id:
            await self._verify_client_ownership(user_id, str(data.client_id))
            
        task_data = data.model_dump(exclude={"labels"})
        task_data["user_id"] = user_id
        
        # Handle labels
        labels = []
        if data.labels:
            for label_name in data.labels:
                label = await self.label_repo.get_or_create(user_id, label_name)
                labels.append(label)
                
        # Create Task
        task = await self.task_repo.create(task_data, labels=labels)
        
        # Create Event
        await self.event_repo.create(TaskEvent(
            task_id=task.id,
            user_id=user_id,
            event_type=TaskEventType.TASK_CREATED
        ))
        
        return TaskResponse.model_validate(task)
        
    async def get(self, user_id: str, task_id: str) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id, load_labels=True)
        if not task or str(task.user_id) != user_id:
            raise NotFoundError("Task not found")
        return TaskResponse.model_validate(task)
        
    async def update(self, user_id: str, task_id: str, data: TaskUpdate) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id, load_labels=True)
        if not task or str(task.user_id) != user_id:
            raise NotFoundError("Task not found")
            
        update_data = data.model_dump(exclude_unset=True, exclude={"labels"})
        
        if "project_id" in update_data and update_data["project_id"]:
            await self._verify_project_ownership(user_id, str(update_data["project_id"]))
        if "client_id" in update_data and update_data["client_id"]:
            await self._verify_client_ownership(user_id, str(update_data["client_id"]))
            
        events_to_create = []
        
        if "status" in update_data and update_data["status"] != task.status:
            old_status = str(task.status.value) if task.status else None
            new_status = str(update_data["status"].value) if update_data["status"] else None
            events_to_create.append(TaskEvent(
                task_id=task.id, user_id=user_id, event_type=TaskEventType.STATUS_CHANGED,
                old_value=old_status, new_value=new_status
            ))
            if update_data["status"] == TaskStatus.COMPLETED:
                update_data["completed_at"] = datetime.now(timezone.utc)
                events_to_create.append(TaskEvent(
                    task_id=task.id, user_id=user_id, event_type=TaskEventType.TASK_COMPLETED
                ))
            elif task.status == TaskStatus.COMPLETED:
                update_data["completed_at"] = None
                
        if "priority" in update_data and update_data["priority"] != task.priority:
            old_priority = str(task.priority.value) if task.priority else None
            new_priority = str(update_data["priority"].value) if update_data["priority"] else None
            events_to_create.append(TaskEvent(
                task_id=task.id, user_id=user_id, event_type=TaskEventType.PRIORITY_CHANGED,
                old_value=old_priority, new_value=new_priority
            ))
            
        if "due_date" in update_data and update_data["due_date"] != task.due_date:
            old_date = task.due_date.isoformat() if task.due_date else None
            new_date = update_data["due_date"].isoformat() if update_data["due_date"] else None
            events_to_create.append(TaskEvent(
                task_id=task.id, user_id=user_id, event_type=TaskEventType.DUE_DATE_CHANGED,
                old_value=old_date, new_value=new_date
            ))
            
        labels = None
        if data.labels is not None:
            labels = []
            for label_name in data.labels:
                label = await self.label_repo.get_or_create(user_id, label_name)
                labels.append(label)
                
        task = await self.task_repo.update(task, update_data, labels=labels)
        
        events_to_create.append(TaskEvent(
            task_id=task.id, user_id=user_id, event_type=TaskEventType.TASK_UPDATED
        ))
        
        for event in events_to_create:
            await self.event_repo.create(event)
            
        return TaskResponse.model_validate(task)
        
    async def change_status(self, user_id: str, task_id: str, data: TaskStatusUpdate) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id, load_labels=True)
        if not task or str(task.user_id) != user_id:
            raise NotFoundError("Task not found")
            
        if task.status == data.status:
            return TaskResponse.model_validate(task)
            
        update_data = {"status": data.status}
        if data.status == TaskStatus.COMPLETED:
            update_data["completed_at"] = datetime.now(timezone.utc)
            await self.event_repo.create(TaskEvent(
                task_id=task.id, user_id=user_id, event_type=TaskEventType.TASK_COMPLETED
            ))
        elif task.status == TaskStatus.COMPLETED:
            update_data["completed_at"] = None
            
        await self.event_repo.create(TaskEvent(
            task_id=task.id, user_id=user_id, event_type=TaskEventType.STATUS_CHANGED,
            old_value=str(task.status.value) if task.status else None, 
            new_value=str(data.status.value)
        ))
        
        task = await self.task_repo.update(task, update_data)
        return TaskResponse.model_validate(task)
        
    async def change_priority(self, user_id: str, task_id: str, data: TaskPriorityUpdate) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id, load_labels=True)
        if not task or str(task.user_id) != user_id:
            raise NotFoundError("Task not found")
            
        if task.priority == data.priority:
            return TaskResponse.model_validate(task)
            
        await self.event_repo.create(TaskEvent(
            task_id=task.id, user_id=user_id, event_type=TaskEventType.PRIORITY_CHANGED,
            old_value=str(task.priority.value) if task.priority else None, 
            new_value=str(data.priority.value)
        ))
        
        task = await self.task_repo.update(task, {"priority": data.priority})
        return TaskResponse.model_validate(task)
        
    async def archive(self, user_id: str, task_id: str) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id, load_labels=True)
        if not task or str(task.user_id) != user_id:
            raise NotFoundError("Task not found")
            
        if not task.archived_at:
            task = await self.task_repo.update(task, {"archived_at": datetime.now(timezone.utc)})
            await self.event_repo.create(TaskEvent(
                task_id=task.id, user_id=user_id, event_type=TaskEventType.TASK_ARCHIVED
            ))
            
        return TaskResponse.model_validate(task)
        
    async def list(self, user_id: str, search: str | None = None, status: TaskStatus | None = None, 
                   priority: TaskPriority | None = None, project_id: str | None = None, 
                   client_id: str | None = None, due_date = None, label: str | None = None, 
                   archived: bool = False, page: int = 1, page_size: int = 20, 
                   sort_by: str = "created_at", sort_order: str = "desc") -> PaginatedResponse[TaskResponse]:
        tasks, total = await self.task_repo.list_by_user(
            user_id=user_id, search=search, status=status, priority=priority, 
            project_id=project_id, client_id=client_id, due_date=due_date, 
            label=label, archived=archived, page=page, page_size=page_size, 
            sort_by=sort_by, sort_order=sort_order
        )
        items = [TaskResponse.model_validate(t) for t in tasks]
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
        
    async def search(self, user_id: str, query: str) -> list[TaskResponse]:
        tasks, _ = await self.task_repo.list_by_user(
            user_id=user_id, search=query, page=1, page_size=20
        )
        return [TaskResponse.model_validate(t) for t in tasks]

    # Convenience aliases for agent tools
    async def create_task(self, user: Any, data: TaskCreate) -> TaskResponse:
        user_id = str(user.id if hasattr(user, "id") else user)
        return await self.create(user_id, data)

    async def get_task(self, user: Any, task_id: Any) -> TaskResponse:
        user_id = str(user.id if hasattr(user, "id") else user)
        return await self.get(user_id, str(task_id))

    async def update_task(self, user: Any, task_id: Any, data: TaskUpdate) -> TaskResponse:
        user_id = str(user.id if hasattr(user, "id") else user)
        return await self.update(user_id, str(task_id), data)

