import uuid
from typing import Optional, List
from app.repositories.repository import CodeRepository
from app.schemas.repository import RepositoryCreate, RepositoryUpdate, Repository
from app.models.user import User
from app.services.project import ProjectService

class RepositoryService:
    def __init__(self, repository: CodeRepository, project_service: ProjectService):
        self.repository = repository
        self.project_service = project_service

    async def get_repository(self, repository_id: uuid.UUID, user: User) -> Optional[Repository]:
        repo = await self.repository.get(repository_id=repository_id)
        if not repo:
            return None
        # Verify user owns the project
        project = await self.project_service.get_project(repo.project_id, user)
        if not project:
            return None
        return repo

    async def list_repositories(self, project_id: uuid.UUID, user: User) -> List[Repository]:
        project = await self.project_service.get_project(project_id, user)
        if not project:
            raise ValueError("Project not found")
        return await self.repository.list_by_project(project_id=project_id)

    async def create_repository(self, user: User, obj_in: RepositoryCreate) -> Repository:
        project = await self.project_service.get_project(obj_in.project_id, user)
        if not project:
            raise ValueError("Project not found")
        return await self.repository.create(obj_in=obj_in)

    async def update_repository(self, repository_id: uuid.UUID, user: User, obj_in: RepositoryUpdate) -> Optional[Repository]:
        db_obj = await self.get_repository(repository_id, user)
        if not db_obj:
            return None
        return await self.repository.update(db_obj=db_obj, obj_in=obj_in)

    async def delete_repository(self, repository_id: uuid.UUID, user: User) -> bool:
        db_obj = await self.get_repository(repository_id, user)
        if not db_obj:
            return False
        await self.repository.delete(db_obj=db_obj)
        return True
