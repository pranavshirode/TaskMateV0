"""Milestone and task dependency service with cycle detection."""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.milestone import Milestone, TaskDependency
from app.models.task import Task
from app.repositories.project import ProjectRepository
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate

logger = logging.getLogger(__name__)


class MilestoneService:
    """Business logic for milestones and task dependencies."""

    VALID_STATUSES = {"OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.project_repo = ProjectRepository(db)

    async def _verify_project_owner(self, user_id: str, project_id: str) -> Any:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by you")
        return project

    async def _get_task(self, task_id: str, user_id: str) -> Task:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError(f"Task '{task_id}' not found")
        return task

    # ── Milestones ────────────────────────────────────────────────────────────

    async def create_milestone(self, user_id: str, data: MilestoneCreate) -> Milestone:
        await self._verify_project_owner(user_id, data.project_id)
        if data.status and data.status not in self.VALID_STATUSES:
            raise ValidationError(f"Invalid status '{data.status}'. Must be one of: {', '.join(self.VALID_STATUSES)}")

        milestone = Milestone(
            project_id=data.project_id,
            user_id=user_id,
            title=data.title.strip(),
            description=data.description,
            status=data.status or "OPEN",
            due_date=data.due_date,
        )
        self.db.add(milestone)
        await self.db.commit()
        return await self.get_milestone(user_id, milestone.id)

    async def list_milestones(self, user_id: str, project_id: str) -> list[Milestone]:
        await self._verify_project_owner(user_id, project_id)
        stmt = (
            select(Milestone)
            .where(Milestone.project_id == project_id, Milestone.user_id == user_id)
            .options(selectinload(Milestone.tasks))
            .order_by(Milestone.due_date.nullslast(), Milestone.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_milestone(self, user_id: str, milestone_id: str) -> Milestone:
        stmt = (
            select(Milestone)
            .where(Milestone.id == milestone_id, Milestone.user_id == user_id)
            .options(selectinload(Milestone.tasks))
        )
        result = await self.db.execute(stmt)
        milestone = result.scalar_one_or_none()
        if not milestone:
            raise NotFoundError("Milestone not found")
        return milestone

    async def update_milestone(self, user_id: str, milestone_id: str, data: MilestoneUpdate) -> Milestone:
        milestone = await self.get_milestone(user_id, milestone_id)

        if data.title is not None:
            milestone.title = data.title.strip()
        if data.description is not None:
            milestone.description = data.description
        if data.status is not None:
            if data.status not in self.VALID_STATUSES:
                raise ValidationError(f"Invalid status '{data.status}'")
            milestone.status = data.status
        if data.due_date is not None:
            milestone.due_date = data.due_date

        milestone.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(milestone)
        return await self.get_milestone(user_id, milestone_id)

    async def delete_milestone(self, user_id: str, milestone_id: str) -> None:
        milestone = await self.get_milestone(user_id, milestone_id)
        await self.db.delete(milestone)
        await self.db.commit()

    # ── Task Dependencies ─────────────────────────────────────────────────────

    async def add_task_dependency(
        self, user_id: str, task_id: str, depends_on_task_id: str
    ) -> TaskDependency:
        """Add a dependency: task_id depends on depends_on_task_id.

        Raises ValidationError if:
        - task_id == depends_on_task_id (self-loop)
        - adding the edge would create a cycle
        - the dependency already exists
        """
        if task_id == depends_on_task_id:
            raise ValidationError("A task cannot depend on itself")

        # Verify both tasks belong to the user
        await self._get_task(task_id, user_id)
        await self._get_task(depends_on_task_id, user_id)

        # Check for duplicate
        stmt = select(TaskDependency).where(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_task_id == depends_on_task_id,
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("This dependency already exists.", code="DUPLICATE_DEPENDENCY")

        # Cycle detection: BFS from depends_on_task_id following task_id edges
        # If we can reach task_id, adding the edge would create a cycle
        if await self._would_create_cycle(task_id, depends_on_task_id):
            raise ValidationError(
                f"Adding this dependency would create a cycle: "
                f"'{depends_on_task_id}' is already (transitively) blocked by '{task_id}'"
            )

        dep = TaskDependency(task_id=task_id, depends_on_task_id=depends_on_task_id)
        self.db.add(dep)
        await self.db.commit()
        await self.db.refresh(dep)

        # Eager-load the depends_on task for the response
        stmt2 = (
            select(TaskDependency)
            .where(TaskDependency.id == dep.id)
            .options(
                selectinload(TaskDependency.depends_on),
                selectinload(TaskDependency.task),
            )
        )
        result2 = await self.db.execute(stmt2)
        return result2.scalar_one()

    async def _would_create_cycle(self, new_task_id: str, new_dep_id: str) -> bool:
        """BFS from new_dep_id via 'task_id depends on depends_on_task_id' edges.

        Returns True if new_task_id is reachable (meaning adding the reverse edge creates a cycle).
        In other words: does new_dep_id already (transitively) depend on new_task_id?
        """
        visited: set[str] = set()
        queue: deque[str] = deque([new_dep_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            # Find all tasks that current depends on
            stmt = select(TaskDependency.depends_on_task_id).where(
                TaskDependency.task_id == current
            )
            result = await self.db.execute(stmt)
            for dep_id in result.scalars():
                if dep_id == new_task_id:
                    return True  # cycle detected
                if dep_id not in visited:
                    queue.append(dep_id)

        return False

    async def remove_task_dependency(
        self, user_id: str, task_id: str, depends_on_task_id: str
    ) -> None:
        await self._get_task(task_id, user_id)
        stmt = select(TaskDependency).where(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_task_id == depends_on_task_id,
        )
        result = await self.db.execute(stmt)
        dep = result.scalar_one_or_none()
        if not dep:
            raise NotFoundError("Dependency not found")
        await self.db.delete(dep)
        await self.db.commit()

    async def get_task_dependencies(self, user_id: str, task_id: str) -> list[TaskDependency]:
        await self._get_task(task_id, user_id)
        stmt = (
            select(TaskDependency)
            .where(TaskDependency.task_id == task_id)
            .options(
                selectinload(TaskDependency.depends_on),
                selectinload(TaskDependency.task),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

