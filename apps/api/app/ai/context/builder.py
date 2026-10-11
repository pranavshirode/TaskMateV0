"""Context Builder for AI prompts.

Builds a minimal, user-scoped representation of the developer's workspace
(projects, clients, active tasks, current date) to provide ground truth
for intent parsing and entity resolution.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.client import ClientService
from app.services.project import ProjectService
from app.services.task import TaskService


class AIContext:
    def __init__(
        self,
        current_date: date,
        day_of_week: str,
        projects: list[dict[str, Any]],
        clients: list[dict[str, Any]],
        recent_tasks: list[dict[str, Any]],
    ):
        self.current_date = current_date
        self.day_of_week = day_of_week
        self.projects = projects
        self.clients = clients
        self.recent_tasks = recent_tasks

    def to_prompt_text(self) -> str:
        """Render context as concise text for LLM system prompt."""
        lines = [
            f"Current Date: {self.current_date.isoformat()} ({self.day_of_week})",
            "",
            "Active Projects:",
        ]
        if self.projects:
            for p in self.projects:
                lines.append(f"- ID: {p['id']}, Name: '{p['name']}'")
        else:
            lines.append("- (No active projects)")

        lines.append("")
        lines.append("Active Clients:")
        if self.clients:
            for c in self.clients:
                lines.append(f"- ID: {c['id']}, Name: '{c['name']}'")
        else:
            lines.append("- (No active clients)")

        lines.append("")
        lines.append("Open / Recent Tasks:")
        if self.recent_tasks:
            for t in self.recent_tasks[:15]:
                proj_note = f" [Project: {t.get('project_name', 'None')}]" if t.get('project_name') else ""
                lines.append(
                    f"- ID: {t['id']}, Title: '{t['title']}', Status: {t['status']}, Priority: {t['priority']}{proj_note}"
                )
        else:
            lines.append("- (No recent tasks)")

        return "\n".join(lines)


class AIContextBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_service = ProjectService(db)
        self.client_service = ClientService(db)
        self.task_service = TaskService(db)

    async def build(self, user_id: str) -> AIContext:
        """Fetch user-scoped context for AI decision making."""
        now = datetime.now(timezone.utc)
        current_date = now.date()
        day_of_week = now.strftime("%A")

        # 1. Fetch user projects
        projects_resp = await self.project_service.list(user_id=user_id, page=1, page_size=50)
        projects = [{"id": p.id, "name": p.name} for p in projects_resp.items]

        # 2. Fetch user clients
        clients_resp = await self.client_service.list(user_id=user_id, page=1, page_size=50)
        clients = [{"id": c.name, "name": c.name, "actual_id": c.id} for c in clients_resp.items]
        # Store both id and name
        clean_clients = [{"id": c.id, "name": c.name} for c in clients_resp.items]

        # 3. Fetch user active tasks
        tasks_resp = await self.task_service.list(user_id=user_id, page=1, page_size=30)
        tasks: list[dict[str, Any]] = []
        proj_map = {p["id"]: p["name"] for p in projects}
        for t in tasks_resp.items:
            tasks.append({
                "id": t.id,
                "title": t.title,
                "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                "priority": t.priority.value if hasattr(t.priority, "value") else str(t.priority),
                "project_id": t.project_id,
                "project_name": proj_map.get(t.project_id, None),
                "due_date": t.due_date.isoformat() if t.due_date else None,
            })

        return AIContext(
            current_date=current_date,
            day_of_week=day_of_week,
            projects=projects,
            clients=clean_clients,
            recent_tasks=tasks,
        )


ContextBuilder = AIContextBuilder

