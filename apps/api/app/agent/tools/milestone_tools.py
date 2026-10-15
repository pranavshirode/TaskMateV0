"""Milestone tools for the agent system.

Enables the AI agent to create and list milestones for projects.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult
from app.schemas.milestone import MilestoneCreate

logger = logging.getLogger(__name__)


class MilestoneCreateTool(AgentTool):
    """Create a new project milestone."""

    @property
    def name(self) -> str:
        return "milestone.create"

    @property
    def description(self) -> str:
        return (
            "Create a new milestone for a project. Requires project_id and title. "
            "Optionally description, status ('OPEN', 'IN_PROGRESS', 'COMPLETED'), and due_date (YYYY-MM-DD)."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "title": {"type": "string", "description": "Milestone title"},
                "description": {"type": "string", "description": "Optional description"},
                "status": {
                    "type": "string",
                    "enum": ["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
                    "description": "Milestone status",
                },
                "due_date": {"type": "string", "format": "date", "description": "Due date in YYYY-MM-DD"},
            },
            "required": ["project_id", "title"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        milestone_service = context.extra.get("milestone_service")
        if not milestone_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Milestone service not available")

        try:
            from datetime import date
            if "due_date" in input_data and isinstance(input_data["due_date"], str):
                input_data["due_date"] = date.fromisoformat(input_data["due_date"])

            data = MilestoneCreate(**input_data)
            milestone = await milestone_service.create_milestone(str(context.user.id), data)
            return ToolResult.ok({
                "id": milestone.id,
                "project_id": milestone.project_id,
                "title": milestone.title,
                "status": milestone.status,
                "due_date": str(milestone.due_date) if milestone.due_date else None,
            })
        except Exception as e:
            logger.error("Failed to create milestone: %s", e)
            return ToolResult.fail("EXECUTION_ERROR", str(e))


class MilestoneListTool(AgentTool):
    """List milestones for a project."""

    @property
    def name(self) -> str:
        return "milestone.list"

    @property
    def description(self) -> str:
        return "List all milestones for a project by project_id."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
            },
            "required": ["project_id"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        milestone_service = context.extra.get("milestone_service")
        if not milestone_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Milestone service not available")

        try:
            milestones = await milestone_service.list_milestones(str(context.user.id), input_data["project_id"])
            return ToolResult.ok({
                "milestones": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "status": m.status,
                        "due_date": str(m.due_date) if m.due_date else None,
                        "task_count": len(getattr(m, "tasks", []) or []),
                    }
                    for m in milestones
                ]
            })
        except Exception as e:
            logger.error("Failed to list milestones: %s", e)
            return ToolResult.fail("EXECUTION_ERROR", str(e))


def get_milestone_tools() -> list[AgentTool]:
    return [MilestoneCreateTool(), MilestoneListTool()]
