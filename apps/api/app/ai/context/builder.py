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
        self.project_notes: list[dict[str, Any]] = []
        self.approved_requirements: list[dict[str, Any]] = []

    def set_project_memory(
        self,
        notes: list[dict[str, Any]],
        requirements: list[dict[str, Any]],
    ) -> None:
        self.project_notes = notes
        self.approved_requirements = requirements

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

        if self.project_notes:
            lines.append("")
            lines.append("Confirmed Project Decisions & Architectural Memory:")
            for n in self.project_notes:
                confirmed_tag = "[Confirmed]" if n.get("is_confirmed") else "[Unconfirmed]"
                lines.append(f"- {confirmed_tag} ({n.get('category')}) {n.get('title')}: {n.get('content')}")

        if self.approved_requirements:
            lines.append("")
            lines.append("Approved Project Requirements:")
            for r in self.approved_requirements[:10]:
                lines.append(f"- [{r.get('key')}] {r.get('title')}: {r.get('description')}")

        lines.append("")
        lines.append("Open / Recent Tasks:")
        if self.recent_tasks:
            for t in self.recent_tasks[:15]:
                proj_note = f" [Project: {t.get('project_name', 'None')}]" if t.get("project_name") else ""
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

    async def build(self, user_id: str, project_id: str | None = None) -> AIContext:
        """Fetch user-scoped context for AI decision making."""
        now = datetime.now(timezone.utc)
        current_date = now.date()
        day_of_week = now.strftime("%A")

        # 1. Fetch user projects
        projects_resp = await self.project_service.list(user_id=user_id, page=1, page_size=50)
        projects = [{"id": p.id, "name": p.name} for p in projects_resp.items]

        # 2. Fetch user clients
        clients_resp = await self.client_service.list(user_id=user_id, page=1, page_size=50)
        clean_clients = [{"id": c.id, "name": c.name} for c in clients_resp.items]

        # 3. Fetch user active tasks
        tasks_resp = await self.task_service.list(user_id=user_id, page=1, page_size=30)
        tasks: list[dict[str, Any]] = []
        proj_map = {p["id"]: p["name"] for p in projects}
        for t in tasks_resp.items:
            tasks.append(
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                    "priority": t.priority.value if hasattr(t.priority, "value") else str(t.priority),
                    "project_id": t.project_id,
                    "project_name": proj_map.get(t.project_id),
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
            )

        ctx = AIContext(
            current_date=current_date,
            day_of_week=day_of_week,
            projects=projects,
            clients=clean_clients,
            recent_tasks=tasks,
        )

        # 4. If project_id provided, fetch persistent context notes & approved requirements
        if project_id:
            try:
                from app.repositories.project_context import ProjectContextNoteRepository
                from app.repositories.requirements import RequirementsAnalysisRepository

                note_repo = ProjectContextNoteRepository(self.db)
                active_notes = await note_repo.get_active_notes_for_context(
                    project_id=project_id, user_id=user_id, limit=10
                )
                notes_data = [
                    {
                        "title": n.title,
                        "content": n.content,
                        "category": n.category.value if hasattr(n.category, "value") else str(n.category),
                        "is_confirmed": n.is_confirmed,
                    }
                    for n in active_notes
                ]

                analysis_repo = RequirementsAnalysisRepository(self.db)
                analyses = await analysis_repo.list_by_project(project_id, user_id)
                approved_reqs = []
                for a in analyses:
                    for r in a.requirements:
                        if r.status.value == "APPROVED" or str(r.status) == "APPROVED":
                            approved_reqs.append(
                                {
                                    "key": r.key,
                                    "title": r.title,
                                    "description": r.description[:200],
                                }
                            )

                ctx.set_project_memory(notes_data, approved_reqs)
            except Exception:
                pass

        return ctx


ContextBuilder = AIContextBuilder
