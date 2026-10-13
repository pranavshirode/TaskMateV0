"""Task tools for the agent system.

These tools wrap TaskService methods, allowing the agent
to create, read, update, and search tasks via natural language.
"""

import logging
import uuid
from datetime import date
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult
from app.schemas.task import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskCreateTool(AgentTool):
    """Create a new task in the user's workspace."""

    @property
    def name(self) -> str:
        return "task.create"

    @property
    def description(self) -> str:
        return (
            "Create a new task. Requires a title. Optionally set description, "
            "status (TODO, IN_PROGRESS, IN_REVIEW, DONE), priority (LOW, MEDIUM, HIGH, URGENT), "
            "due_date (YYYY-MM-DD), estimated_minutes, project_id, and client_id."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"],
                    "description": "Task status",
                },
                "priority": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"],
                    "description": "Task priority",
                },
                "due_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Due date in YYYY-MM-DD format",
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": "Estimated time in minutes",
                },
                "project_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Project UUID to associate this task with",
                },
                "client_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Client UUID to associate this task with",
                },
                "source": {"type": "string", "description": "Source of the task (e.g. 'github')"},
                "external_reference": {
                    "type": "string",
                    "description": "External reference (e.g. 'issue#42')",
                },
            },
            "required": ["title"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            # Parse date if provided
            if "due_date" in input_data and isinstance(input_data["due_date"], str):
                input_data["due_date"] = date.fromisoformat(input_data["due_date"])

            # Parse UUIDs
            for field in ("project_id", "client_id"):
                if field in input_data and isinstance(input_data[field], str):
                    input_data[field] = uuid.UUID(input_data[field])

            task_in = TaskCreate(**input_data)
            task = await task_service.create_task(context.user, task_in)
            return ToolResult.ok(
                {
                    "task_id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": str(task.due_date) if task.due_date else None,
                    "project_id": str(task.project_id) if task.project_id else None,
                    "message": f"Task '{task.title}' created successfully.",
                }
            )
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("task.create failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to create task: {e}")


class TaskGetTool(AgentTool):
    """Get details of a single task by ID."""

    @property
    def name(self) -> str:
        return "task.get"

    @property
    def description(self) -> str:
        return "Get details of a task by its UUID."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the task to retrieve",
                },
            },
            "required": ["task_id"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            task_id = uuid.UUID(input_data["task_id"])
            task = await task_service.get_task(task_id, context.user)
            if not task:
                return ToolResult.fail("NOT_FOUND", f"Task {task_id} not found")
            return ToolResult.ok(task.model_dump(mode="json"))
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("task.get failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to get task: {e}")


class TaskSearchTool(AgentTool):
    """Search and filter tasks."""

    @property
    def name(self) -> str:
        return "task.search"

    @property
    def description(self) -> str:
        return (
            "Search tasks with optional filters: search query, status, priority, "
            "project_id, client_id. Returns a list of matching tasks."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search query for title/description"},
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"],
                    "description": "Filter by status",
                },
                "priority": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"],
                    "description": "Filter by priority",
                },
                "project_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Filter by project UUID",
                },
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
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            # Parse UUIDs
            for field in ("project_id", "client_id"):
                if field in input_data and isinstance(input_data[field], str):
                    input_data[field] = uuid.UUID(input_data[field])

            limit = input_data.pop("limit", 20)
            items, total = await task_service.list_tasks(
                user=context.user,
                skip=0,
                limit=limit,
                **input_data,
            )
            return ToolResult.ok(
                {
                    "tasks": [t.model_dump(mode="json") for t in items],
                    "total": total,
                    "returned": len(items),
                }
            )
        except Exception as e:
            logger.exception("task.search failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to search tasks: {e}")


class TaskUpdateTool(AgentTool):
    """Update an existing task."""

    @property
    def name(self) -> str:
        return "task.update"

    @property
    def description(self) -> str:
        return (
            "Update fields of an existing task. Provide the task_id and any fields "
            "to update: title, description, status, priority, due_date, estimated_minutes, "
            "project_id, client_id."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the task to update",
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"],
                },
                "priority": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"],
                },
                "due_date": {"type": "string", "format": "date"},
                "estimated_minutes": {"type": "integer"},
                "actual_minutes": {"type": "integer"},
                "project_id": {"type": "string", "format": "uuid"},
                "client_id": {"type": "string", "format": "uuid"},
            },
            "required": ["task_id"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            task_id = uuid.UUID(input_data.pop("task_id"))

            # Parse date
            if "due_date" in input_data and isinstance(input_data["due_date"], str):
                input_data["due_date"] = date.fromisoformat(input_data["due_date"])

            # Parse UUIDs
            for field in ("project_id", "client_id"):
                if field in input_data and isinstance(input_data[field], str):
                    input_data[field] = uuid.UUID(input_data[field])

            task_update = TaskUpdate(**input_data)
            task = await task_service.update_task(task_id, context.user, task_update)
            if not task:
                return ToolResult.fail("NOT_FOUND", f"Task {task_id} not found")
            return ToolResult.ok(
                {
                    "task_id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "message": f"Task '{task.title}' updated successfully.",
                }
            )
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("task.update failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to update task: {e}")


class TaskChangeStatusTool(AgentTool):
    """Change a task's status."""

    @property
    def name(self) -> str:
        return "task.change_status"

    @property
    def description(self) -> str:
        return "Change the status of a task. Valid statuses: TODO, IN_PROGRESS, IN_REVIEW, DONE."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the task",
                },
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"],
                    "description": "New status",
                },
            },
            "required": ["task_id", "status"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            task_id = uuid.UUID(input_data["task_id"])
            task = await task_service.change_status(task_id, context.user, input_data["status"])
            if not task:
                return ToolResult.fail("NOT_FOUND", f"Task {task_id} not found")
            return ToolResult.ok(
                {
                    "task_id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "message": f"Task '{task.title}' status changed to {task.status}.",
                }
            )
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("task.change_status failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to change status: {e}")


class TaskChangePriorityTool(AgentTool):
    """Change a task's priority."""

    @property
    def name(self) -> str:
        return "task.change_priority"

    @property
    def description(self) -> str:
        return "Change the priority of a task. Valid priorities: LOW, MEDIUM, HIGH, URGENT."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the task",
                },
                "priority": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"],
                    "description": "New priority",
                },
            },
            "required": ["task_id", "priority"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        task_service = context.extra.get("task_service")
        if not task_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Task service not available")

        try:
            task_id = uuid.UUID(input_data["task_id"])
            task = await task_service.change_priority(task_id, context.user, input_data["priority"])
            if not task:
                return ToolResult.fail("NOT_FOUND", f"Task {task_id} not found")
            return ToolResult.ok(
                {
                    "task_id": str(task.id),
                    "title": task.title,
                    "priority": task.priority,
                    "message": f"Task '{task.title}' priority changed to {task.priority}.",
                }
            )
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("task.change_priority failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to change priority: {e}")


def get_task_tools() -> list[AgentTool]:
    """Return all task tools for registry registration."""
    return [
        TaskCreateTool(),
        TaskGetTool(),
        TaskSearchTool(),
        TaskUpdateTool(),
        TaskChangeStatusTool(),
        TaskChangePriorityTool(),
    ]
