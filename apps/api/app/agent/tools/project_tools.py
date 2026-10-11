"""Project tools for the agent system.

These tools wrap ProjectService methods, allowing the agent
to read and list projects via natural language.
"""

import uuid
import logging
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult

logger = logging.getLogger(__name__)


class ProjectGetTool(AgentTool):
    """Get details of a single project by ID."""

    @property
    def name(self) -> str:
        return "project.get"

    @property
    def description(self) -> str:
        return "Get details of a project by its UUID."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the project to retrieve",
                },
            },
            "required": ["project_id"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        project_service = context.extra.get("project_service")
        if not project_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Project service not available")

        try:
            project_id = uuid.UUID(input_data["project_id"])
            project = await project_service.get_project(project_id, context.user)
            if not project:
                return ToolResult.fail("NOT_FOUND", f"Project {project_id} not found")
            return ToolResult.ok(project.model_dump(mode="json"))
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("project.get failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to get project: {e}")


class ProjectListTool(AgentTool):
    """List projects."""

    @property
    def name(self) -> str:
        return "project.list"

    @property
    def description(self) -> str:
        return (
            "List and search projects with optional filters: search query, status, client_id."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search query for project name/description"},
                "status": {"type": "string", "description": "Filter by status"},
                "client_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Filter by client UUID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 20)",
                },
            },
            "required": [],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        project_service = context.extra.get("project_service")
        if not project_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Project service not available")

        try:
            if "client_id" in input_data and isinstance(input_data["client_id"], str):
                input_data["client_id"] = uuid.UUID(input_data["client_id"])

            limit = input_data.pop("limit", 20)
            items, total = await project_service.list_projects(
                user=context.user,
                skip=0,
                limit=limit,
                **input_data,
            )
            return ToolResult.ok({
                "projects": [p.model_dump(mode="json") for p in items],
                "total": total,
                "returned": len(items),
            })
        except Exception as e:
            logger.exception("project.list failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to list projects: {e}")


def get_project_tools() -> list[AgentTool]:
    """Return all project tools for registry registration."""
    return [ProjectGetTool(), ProjectListTool()]

