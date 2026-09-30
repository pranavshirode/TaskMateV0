from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import ProjectRepository
from app.repositories.client import ClientRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse
from app.schemas.common import PaginatedResponse
from app.core.errors import NotFoundError, ValidationError
from app.models.enums import ProjectStatus

class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.client_repo = ClientRepository(session)
        
    async def _verify_client_ownership(self, user_id: str, client_id: str) -> None:
        client = await self.client_repo.get_by_id(client_id)
        if not client or str(client.user_id) != user_id:
            raise ValidationError("Invalid client_id or client does not belong to user")
            
    async def create(self, user_id: str, data: ProjectCreate) -> ProjectResponse:
        if data.client_id:
            await self._verify_client_ownership(user_id, str(data.client_id))
            
        project_data = data.model_dump()
        project_data["user_id"] = user_id
        project = await self.project_repo.create(project_data)
        return ProjectResponse.model_validate(project)
        
    async def get(self, user_id: str, project_id: str) -> ProjectDetailResponse:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise NotFoundError("Project not found")
            
        task_summary = await self.project_repo.get_task_summary(project_id)
        
        base = ProjectResponse.model_validate(project)
        return ProjectDetailResponse(**base.model_dump(), task_summary=task_summary)
        
    async def update(self, user_id: str, project_id: str, data: ProjectUpdate) -> ProjectResponse:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise NotFoundError("Project not found")
            
        update_data = data.model_dump(exclude_unset=True)
        
        if "client_id" in update_data and update_data["client_id"]:
            await self._verify_client_ownership(user_id, str(update_data["client_id"]))
            
        if "status" in update_data:
            if update_data["status"] == ProjectStatus.ARCHIVED and project.status != ProjectStatus.ARCHIVED:
                update_data["archived_at"] = datetime.now(timezone.utc)
            elif update_data["status"] != ProjectStatus.ARCHIVED and project.status == ProjectStatus.ARCHIVED:
                update_data["archived_at"] = None
                
        project = await self.project_repo.update(project, update_data)
        return ProjectResponse.model_validate(project)
        
    async def archive(self, user_id: str, project_id: str) -> ProjectResponse:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise NotFoundError("Project not found")
            
        if project.status != ProjectStatus.ARCHIVED:
            project = await self.project_repo.update(project, {
                "status": ProjectStatus.ARCHIVED,
                "archived_at": datetime.now(timezone.utc)
            })
        return ProjectResponse.model_validate(project)
        
    async def list(self, user_id: str, search: str | None = None, status: ProjectStatus | None = None,
                   client_id: str | None = None, page: int = 1, page_size: int = 20,
                   sort_by: str = "created_at", sort_order: str = "desc") -> PaginatedResponse[ProjectResponse]:
        projects, total = await self.project_repo.list_by_user(
            user_id=user_id, search=search, status=status, client_id=client_id,
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items = [ProjectResponse.model_validate(p) for p in projects]
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
        
    async def get_active(self, user_id: str) -> list[ProjectResponse]:
        projects, _ = await self.project_repo.list_by_user(
            user_id=user_id, status=ProjectStatus.ACTIVE, page=1, page_size=100
        )
        # Assuming list_by_user handles filtering out archived properly if requested, or filtering by ACTIVE status
        return [ProjectResponse.model_validate(p) for p in projects if p.status == ProjectStatus.ACTIVE and p.archived_at is None]

