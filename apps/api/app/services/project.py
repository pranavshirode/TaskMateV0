import uuid
from typing import Optional, Tuple, List
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, Project
from app.models.user import User
from app.services.client import ClientService

class ProjectService:
    def __init__(self, repository: ProjectRepository, client_service: ClientService):
        self.repository = repository
        self.client_service = client_service

    async def get_project(self, project_id: uuid.UUID, user: User) -> Optional[Project]:
        return await self.repository.get(project_id=project_id, user_id=user.id)

    async def list_projects(self, user: User, skip: int = 0, limit: int = 20, client_id: Optional[uuid.UUID] = None, status: Optional[str] = None, search: Optional[str] = None) -> Tuple[List[Project], int]:
        items = await self.repository.list(user_id=user.id, skip=skip, limit=limit, client_id=client_id, status=status, search=search)
        total = await self.repository.count(user_id=user.id, client_id=client_id, status=status, search=search)
        return items, total

    async def create_project(self, user: User, obj_in: ProjectCreate) -> Project:
        if obj_in.client_id:
            client = await self.client_service.get_client(obj_in.client_id, user)
            if not client:
                raise ValueError("Client not found")
        return await self.repository.create(user_id=user.id, obj_in=obj_in)

    async def update_project(self, project_id: uuid.UUID, user: User, obj_in: ProjectUpdate) -> Optional[Project]:
        db_obj = await self.get_project(project_id, user)
        if not db_obj:
            return None
        if obj_in.client_id:
            client = await self.client_service.get_client(obj_in.client_id, user)
            if not client:
                raise ValueError("Client not found")
        return await self.repository.update(db_obj=db_obj, obj_in=obj_in)

    async def archive_project(self, project_id: uuid.UUID, user: User) -> Optional[Project]:
        db_obj = await self.get_project(project_id, user)
        if not db_obj:
            return None
        return await self.repository.archive(db_obj=db_obj)
