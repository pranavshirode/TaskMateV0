"""Permission layer for the agent system."""

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.base import ToolPermission
from app.agent.tools.registry import ToolRegistry
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.models.project import Project
from app.models.repository import Repository
from app.models.user import User
from app.services.github_integration import GitHubIntegrationService
from app.services.project import ProjectService


@dataclass
class PermissionResult:
    allowed: bool
    requires_approval: bool = False
    reason: str | None = None


class ToolPermissionService:
    """Service to handle agent tool permissions and approval checks."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        project_service: ProjectService,
        github_service: GitHubIntegrationService,
        db: AsyncSession,
        settings: Settings,
    ):
        self.tool_registry = tool_registry
        self.project_service = project_service
        self.github_service = github_service
        self.db = db
        self.settings = settings

    async def check_tool_permission(self, user: User, tool_name: str, tool_input: dict[str, Any]) -> PermissionResult:
        """Check if the user is allowed to execute the tool with given input."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return PermissionResult(allowed=False, reason=f"Tool '{tool_name}' not found")

        requires_approval = False
        if tool.permission == ToolPermission.WRITE:
            requires_approval = self.settings.AGENT_REQUIRE_APPROVAL_FOR_WRITES
        elif tool.permission == ToolPermission.DESTRUCTIVE:
            requires_approval = True  # Destructive actions always require approval

        # External MCP actions (send email, create issue, edit a doc...) always need the user's approval,
        # even if AGENT_REQUIRE_APPROVAL_FOR_WRITES is turned off. Only server-declared read-only tools run directly.
        if tool.name.startswith("mcp.") and tool.permission != ToolPermission.READ:
            requires_approval = True

        # Check GitHub tools
        if tool.name.startswith("github."):
            integration = await self.github_service.get_integration(user)
            if not integration:
                return PermissionResult(allowed=False, reason="GitHub account is not connected")

        # Check Project tools (if referencing a specific project)
        if tool.name in ("project.get", "project.update"):
            project_id_str = tool_input.get("project_id")
            if project_id_str and not await self._can_access_project(user, project_id_str):
                return PermissionResult(allowed=False, reason="Project not found or access denied")

        if tool.name == "task.create":
            project_id_str = tool_input.get("project_id")
            if project_id_str and not await self._can_access_project(user, project_id_str):
                return PermissionResult(allowed=False, reason="Project not found or access denied")

        return PermissionResult(allowed=True, requires_approval=requires_approval)

    async def _can_access_project(self, user: User, project_id: str) -> bool:
        try:
            uuid.UUID(str(project_id))
        except ValueError:
            return False  # Malformed ids from the model are a denial, not a crash.
        try:
            await self.project_service.get_project(user, project_id)
        except NotFoundError:
            return False
        return True

    async def can_access_repository(self, user: User, repository_id: uuid.UUID) -> bool:
        """Check if user has access to a specific repository."""
        stmt = select(Repository).join(Project).where(Repository.id == repository_id, Project.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
