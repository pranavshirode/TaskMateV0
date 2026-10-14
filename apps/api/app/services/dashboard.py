from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ProjectStatus
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.schemas.dashboard import DashboardResponse
from app.schemas.project import ProjectDetailResponse, ProjectResponse
from app.schemas.task import TaskResponse


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.project_repo = ProjectRepository(session)

    async def get_today_dashboard(self, user_id: str) -> DashboardResponse:
        due_today = await self.task_repo.get_due_today(user_id)
        overdue = await self.task_repo.get_overdue(user_id)
        high_priority = await self.task_repo.get_high_priority(user_id)
        recently_updated = await self.task_repo.get_recently_updated(user_id, limit=10)

        # Get active projects
        active_projects, _ = await self.project_repo.list_by_user(
            user_id=user_id,
            status=ProjectStatus.ACTIVE,
            page=1,
            page_size=10,
            sort_by="updated_at",
            sort_order="desc",
        )

        return DashboardResponse(
            date=date.today(),
            due_today=[TaskResponse.model_validate(t) for t in due_today],
            overdue=[TaskResponse.model_validate(t) for t in overdue],
            high_priority=[TaskResponse.model_validate(t) for t in high_priority],
            active_projects=[
                ProjectDetailResponse(
                    **ProjectResponse.model_validate(p).model_dump(),
                    task_summary=await self.project_repo.get_task_summary(p.id),
                )
                for p in active_projects
            ],
            recently_updated=[TaskResponse.model_validate(t) for t in recently_updated],
        )
