from datetime import date

from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.enums import ProjectStatus, TaskStatus
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def create(self, data: dict) -> Project:
        project = Project(**data)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def update(self, project: Project, data: dict) -> Project:
        for key, value in data.items():
            setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def list_by_user(
        self,
        user_id: str,
        search: str | None = None,
        status: ProjectStatus | None = None,
        client_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Project], int]:
        query = select(self.model).where(self.model.user_id == user_id)

        if search:
            query = query.where(self.model.name.ilike(f"%{search}%"))

        if status:
            query = query.where(self.model.status == status)

        if client_id:
            query = query.where(self.model.client_id == client_id)

        # Sorting — whitelist allowed fields
        sort_column = getattr(self.model, sort_by, self.model.created_at)
        if sort_by not in ["created_at", "updated_at", "name", "deadline"]:
            sort_column = self.model.created_at

        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return await self.paginate(query, page, page_size)

    async def get_task_summary(self, project_id: str) -> dict:
        from app.models.task import Task

        base = select(func.count()).where(
            Task.project_id == project_id, Task.archived_at.is_(None)
        )

        total = (await self.session.execute(base)).scalar_one()
        completed = (
            await self.session.execute(
                base.where(Task.status == TaskStatus.COMPLETED)
            )
        ).scalar_one()
        in_progress = (
            await self.session.execute(
                base.where(Task.status == TaskStatus.IN_PROGRESS)
            )
        ).scalar_one()
        overdue = (
            await self.session.execute(
                base.where(
                    Task.due_date < date.today(),
                    Task.status != TaskStatus.COMPLETED,
                )
            )
        ).scalar_one()

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
        }
