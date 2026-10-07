"""Context builder for AI interactions.

Builds relevant, minimal, user-scoped context from existing
business services. Never accesses the database directly.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from app.ai.schemas.responses import ContextSummary
from app.models.user import User
from app.services.client import ClientService
from app.services.dashboard import DashboardService
from app.services.project import ProjectService
from app.services.task import TaskService

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceContext:
    """Structured workspace context for AI prompts."""
    formatted_text: str  # Human-readable text for the LLM prompt
    summary: ContextSummary  # Summary stats for the API response
    projects: list[dict[str, Any]]  # Simplified project data
    clients: list[dict[str, Any]]  # Simplified client data
    recent_tasks: list[dict[str, Any]]  # Simplified task data
    today_data: dict[str, Any]  # Dashboard data


class ContextBuilder:
    """Builds workspace context for AI interactions.

    Uses existing business services to fetch user-scoped data.
    Formats context for inclusion in AI prompts while keeping
    the data minimal and relevant.

    This class NEVER:
    - Accesses the database directly
    - Exposes data from other users
    - Sends full descriptions or large text blocks to the LLM
    """

    def __init__(
        self,
        task_service: TaskService,
        project_service: ProjectService,
        client_service: ClientService,
        dashboard_service: DashboardService,
    ):
        self.task_service = task_service
        self.project_service = project_service
        self.client_service = client_service
        self.dashboard_service = dashboard_service

    async def build_context(self, user: User) -> WorkspaceContext:
        """Build complete workspace context for a user.

        Fetches projects, clients, recent tasks, and today's dashboard
        data, then formats it for AI prompt inclusion.
        """
        # Fetch data from services (all user-scoped)
        projects_data = await self._get_projects(user)
        clients_data = await self._get_clients(user)
        tasks_data = await self._get_recent_tasks(user)
        today_data = await self._get_today_data(user)

        # Build formatted text for the prompt
        formatted_text = self._format_context(
            projects_data, clients_data, tasks_data, today_data
        )

        # Build summary for the response
        summary = ContextSummary(
            task_count=len(tasks_data),
            project_count=len(projects_data),
            overdue_count=len(today_data.get("overdue", [])),
            due_today_count=len(today_data.get("due_today", [])),
        )

        return WorkspaceContext(
            formatted_text=formatted_text,
            summary=summary,
            projects=projects_data,
            clients=clients_data,
            recent_tasks=tasks_data,
            today_data=today_data,
        )

    async def _get_projects(self, user: User) -> list[dict[str, Any]]:
        """Get simplified project list for context."""
        try:
            projects, _ = await self.project_service.list_projects(
                user, skip=0, limit=50
            )
            return [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "client_id": str(p.client_id) if p.client_id else None,
                }
                for p in projects
            ]
        except Exception:
            logger.warning("Failed to fetch projects for context", exc_info=True)
            return []

    async def _get_clients(self, user: User) -> list[dict[str, Any]]:
        """Get simplified client list for context."""
        try:
            clients, _ = await self.client_service.list_clients(
                user, skip=0, limit=50
            )
            return [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "company_name": c.company_name,
                    "status": c.status,
                }
                for c in clients
            ]
        except Exception:
            logger.warning("Failed to fetch clients for context", exc_info=True)
            return []

    async def _get_recent_tasks(self, user: User) -> list[dict[str, Any]]:
        """Get simplified recent task list for context."""
        try:
            tasks, _ = await self.task_service.list_tasks(
                user, skip=0, limit=30
            )
            return [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": str(t.due_date) if t.due_date else None,
                    "project_id": str(t.project_id) if t.project_id else None,
                }
                for t in tasks
            ]
        except Exception:
            logger.warning("Failed to fetch tasks for context", exc_info=True)
            return []

    async def _get_today_data(self, user: User) -> dict[str, Any]:
        """Get today's dashboard data for context."""
        try:
            data = await self.dashboard_service.get_today_dashboard(user)
            # Simplify the data to avoid sending too much to LLM
            result: dict[str, Any] = {"date": data.get("date", "")}
            for key in ["due_today", "overdue", "high_priority"]:
                items = data.get(key, [])
                result[key] = [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "status": t.status,
                        "priority": t.priority,
                        "due_date": str(t.due_date) if t.due_date else None,
                    }
                    for t in items
                ]
            result["active_projects"] = [
                {"id": str(p.id), "name": p.name, "status": p.status}
                for p in data.get("active_projects", [])
            ]
            return result
        except Exception:
            logger.warning("Failed to fetch today data for context", exc_info=True)
            return {}

    def _format_context(
        self,
        projects: list[dict],
        clients: list[dict],
        tasks: list[dict],
        today_data: dict,
    ) -> str:
        """Format context data as structured text for the AI prompt."""
        sections = []

        # Projects
        if projects:
            project_lines = []
            for p in projects:
                project_lines.append(f"  - {p['name']} (status: {p['status']})")
            sections.append("Active Projects:\n" + "\n".join(project_lines))
        else:
            sections.append("Active Projects: None")

        # Clients
        if clients:
            client_lines = []
            for c in clients:
                company = f" ({c['company_name']})" if c.get('company_name') else ""
                client_lines.append(f"  - {c['name']}{company}")
            sections.append("Clients:\n" + "\n".join(client_lines))
        else:
            sections.append("Clients: None")

        # Today's overview
        due_today = today_data.get("due_today", [])
        overdue = today_data.get("overdue", [])
        high_priority = today_data.get("high_priority", [])

        if due_today:
            lines = [f"  - {t['title']} (priority: {t['priority']})" for t in due_today]
            sections.append("Due Today:\n" + "\n".join(lines))

        if overdue:
            lines = [f"  - {t['title']} (due: {t.get('due_date', 'unknown')}, priority: {t['priority']})" for t in overdue]
            sections.append("Overdue:\n" + "\n".join(lines))

        if high_priority:
            lines = [f"  - {t['title']} (status: {t['status']}, due: {t.get('due_date', 'none')})" for t in high_priority]
            sections.append("High Priority Tasks:\n" + "\n".join(lines))

        # Recent tasks
        if tasks:
            task_lines = []
            for t in tasks[:15]:  # Limit to 15 for prompt size
                due = f", due: {t['due_date']}" if t.get('due_date') else ""
                task_lines.append(f"  - {t['title']} (status: {t['status']}, priority: {t['priority']}{due})")
            sections.append("Recent Tasks:\n" + "\n".join(task_lines))

        return "\n\n".join(sections)

    def get_project_names(self, context: WorkspaceContext) -> str:
        """Get a formatted list of project names for prompts."""
        if not context.projects:
            return "No projects found"
        return ", ".join(p["name"] for p in context.projects)

    def get_client_names(self, context: WorkspaceContext) -> str:
        """Get a formatted list of client names for prompts."""
        if not context.clients:
            return "No clients found"
        return ", ".join(c["name"] for c in context.clients)

    def get_task_names(self, context: WorkspaceContext) -> str:
        """Get a formatted list of task titles for prompts."""
        if not context.recent_tasks:
            return "No tasks found"
        return ", ".join(t["title"] for t in context.recent_tasks[:20])
