import uuid
from typing import Optional, Tuple, List
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate, Task, TaskEvent
from app.models.user import User
from app.services.client import ClientService
from app.services.project import ProjectService

class TaskService:
    def __init__(self, repository: TaskRepository, client_service: ClientService, project_service: ProjectService):
        self.repository = repository
        self.client_service = client_service
        self.project_service = project_service

    async def get_task(self, task_id: uuid.UUID, user: User) -> Optional[Task]:
        return await self.repository.get(task_id=task_id, user_id=user.id)

    async def list_tasks(self, user: User, skip: int = 0, limit: int = 20,
                         project_id: Optional[uuid.UUID] = None, client_id: Optional[uuid.UUID] = None,
                         status: Optional[str] = None, priority: Optional[str] = None,
                         search: Optional[str] = None) -> Tuple[List[Task], int]:
        items = await self.repository.list(user_id=user.id, skip=skip, limit=limit,
                                           project_id=project_id, client_id=client_id,
                                           status=status, priority=priority, search=search)
        total = await self.repository.count(user_id=user.id, project_id=project_id, client_id=client_id,
                                            status=status, priority=priority, search=search)
        return items, total

    async def _validate_relations(self, user: User, client_id: Optional[uuid.UUID], project_id: Optional[uuid.UUID]):
        if client_id:
            client = await self.client_service.get_client(client_id, user)
            if not client:
                raise ValueError("Client not found")
        if project_id:
            project = await self.project_service.get_project(project_id, user)
            if not project:
                raise ValueError("Project not found")

    async def create_task(self, user: User, obj_in: TaskCreate) -> Task:
        await self._validate_relations(user, obj_in.client_id, obj_in.project_id)
        return await self.repository.create(user_id=user.id, obj_in=obj_in)

    async def update_task(self, task_id: uuid.UUID, user: User, obj_in: TaskUpdate) -> Optional[Task]:
        db_obj = await self.get_task(task_id, user)
        if not db_obj:
            return None
        await self._validate_relations(user, obj_in.client_id, obj_in.project_id)
        return await self.repository.update(db_obj=db_obj, user_id=user.id, obj_in=obj_in)

    async def change_status(self, task_id: uuid.UUID, user: User, new_status: str) -> Optional[Task]:
        db_obj = await self.get_task(task_id, user)
        if not db_obj:
            return None
        return await self.repository.change_status(db_obj=db_obj, user_id=user.id, new_status=new_status)

    async def change_priority(self, task_id: uuid.UUID, user: User, new_priority: str) -> Optional[Task]:
        db_obj = await self.get_task(task_id, user)
        if not db_obj:
            return None
        return await self.repository.change_priority(db_obj=db_obj, user_id=user.id, new_priority=new_priority)

    async def archive_task(self, task_id: uuid.UUID, user: User) -> Optional[Task]:
        db_obj = await self.get_task(task_id, user)
        if not db_obj:
            return None
        return await self.repository.archive(db_obj=db_obj, user_id=user.id)

    async def get_task_events(self, task_id: uuid.UUID, user: User) -> List[TaskEvent]:
        db_obj = await self.get_task(task_id, user)
        if not db_obj:
            raise ValueError("Task not found")
        return await self.repository.get_events(task_id=task_id, user_id=user.id)
