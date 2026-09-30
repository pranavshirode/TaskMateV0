from __future__ import annotations

from datetime import date

from sqlalchemy import select, desc, asc, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.task_label import TaskLabel
from app.models.enums import TaskStatus, TaskPriority
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_id(self, id: str, load_labels: bool = False) -> Task | None:
        query = select(self.model).where(self.model.id == id)
        if load_labels:
            query = query.options(selectinload(self.model.labels))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict | Task, labels: list | None = None) -> Task:
        if isinstance(data, dict):
            task = Task(**data)
        else:
            task = data
        if labels:
            task.labels = labels
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task, ["labels"])
        return task

    async def update(
        self, task: Task, data: dict, labels: list | None = None
    ) -> Task:
        for key, value in data.items():
            setattr(task, key, value)
        if labels is not None:
            task.labels = labels
        await self.session.commit()
        await self.session.refresh(task, ["labels"])
        return task

    async def get_by_id_and_user(self, id: str, user_id: str) -> Task | None:
        result = await self.session.execute(
            select(self.model)
            .where(self.model.id == id, self.model.user_id == user_id)
            .options(selectinload(self.model.labels))
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: str,
        search: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        project_id: str | None = None,
        client_id: str | None = None,
        due_date: date | None = None,
        label: str | None = None,
        archived: bool = False,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Task], int]:
        query = select(self.model).where(self.model.user_id == user_id)

        if not archived:
            query = query.where(self.model.archived_at.is_(None))

        if search:
            query = query.where(
                or_(
                    self.model.title.ilike(f"%{search}%"),
                    self.model.description.ilike(f"%{search}%"),
                )
            )

        if status:
            query = query.where(self.model.status == status)

        if priority:
            query = query.where(self.model.priority == priority)

        if project_id:
            query = query.where(self.model.project_id == project_id)

        if client_id:
            query = query.where(self.model.client_id == client_id)

        if due_date:
            query = query.where(self.model.due_date == due_date)

        if label:
            query = query.join(self.model.labels).where(TaskLabel.name == label)

        query = query.options(selectinload(self.model.labels))

        # Sorting
        if sort_by == "priority":
            priority_order = case(
                (self.model.priority == TaskPriority.URGENT, 1),
                (self.model.priority == TaskPriority.HIGH, 2),
                (self.model.priority == TaskPriority.MEDIUM, 3),
                (self.model.priority == TaskPriority.LOW, 4),
                else_=5,
            )
            sort_column = priority_order
        else:
            sort_column = getattr(self.model, sort_by, self.model.created_at)
            if sort_by not in ["created_at", "updated_at", "due_date", "title"]:
                sort_column = self.model.created_at

        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return await self.paginate(query, page, page_size)

    async def get_due_today(self, user_id: str) -> list[Task]:
        query = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.due_date == date.today(),
                self.model.status != TaskStatus.COMPLETED,
                self.model.archived_at.is_(None),
            )
            .options(selectinload(self.model.labels))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue(self, user_id: str) -> list[Task]:
        query = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.due_date < date.today(),
                self.model.status != TaskStatus.COMPLETED,
                self.model.archived_at.is_(None),
            )
            .options(selectinload(self.model.labels))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_high_priority(self, user_id: str) -> list[Task]:
        query = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.priority.in_([TaskPriority.HIGH, TaskPriority.URGENT]),
                self.model.status != TaskStatus.COMPLETED,
                self.model.archived_at.is_(None),
            )
            .options(selectinload(self.model.labels))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recently_updated(
        self, user_id: str, limit: int = 10
    ) -> list[Task]:
        query = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.archived_at.is_(None),
            )
            .order_by(desc(self.model.updated_at))
            .limit(limit)
            .options(selectinload(self.model.labels))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
