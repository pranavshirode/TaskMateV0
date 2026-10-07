import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone, date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.project import Project

class DashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_today_data(self, user_id: uuid.UUID) -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date()

        # Base condition for active tasks
        active_task_cond = and_(
            Task.user_id == user_id,
            Task.status != "COMPLETED",
            Task.archived_at.is_(None)
        )

        # 1. Due today
        stmt_due_today = select(Task).where(
            active_task_cond,
            Task.due_date == today
        )
        due_today = (await self.session.execute(stmt_due_today)).scalars().all()

        # 2. Overdue
        stmt_overdue = select(Task).where(
            active_task_cond,
            Task.due_date < today
        )
        overdue = (await self.session.execute(stmt_overdue)).scalars().all()

        # 3. High priority
        stmt_high_priority = select(Task).where(
            active_task_cond,
            Task.priority.in_(["HIGH", "URGENT"])
        )
        high_priority = (await self.session.execute(stmt_high_priority)).scalars().all()

        # 4. Recently updated
        from sqlalchemy import desc
        stmt_recent = select(Task).where(
            Task.user_id == user_id,
            Task.archived_at.is_(None)
        ).order_by(desc(Task.updated_at)).limit(5)
        recent = (await self.session.execute(stmt_recent)).scalars().all()

        # 5. Active projects
        stmt_active_projects = select(Project).where(
            Project.user_id == user_id,
            Project.status == "ACTIVE",
            Project.archived_at.is_(None)
        )
        active_projects = (await self.session.execute(stmt_active_projects)).scalars().all()

        return {
            "date": today.isoformat(),
            "due_today": list(due_today),
            "overdue": list(overdue),
            "high_priority": list(high_priority),
            "recently_updated": list(recent),
            "active_projects": list(active_projects)
        }
