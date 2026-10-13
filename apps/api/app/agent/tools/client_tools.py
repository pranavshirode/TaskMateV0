"""Client tools for the agent system.

These tools wrap ClientService methods, allowing the agent
to read and list clients via natural language.
"""

import logging
import uuid
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult

logger = logging.getLogger(__name__)


class ClientGetTool(AgentTool):
    """Get details of a single client by ID."""

    @property
    def name(self) -> str:
        return "client.get"

    @property
    def description(self) -> str:
        return "Get details of a client by its UUID."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the client to retrieve",
                },
            },
            "required": ["client_id"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        client_service = context.extra.get("client_service")
        if not client_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Client service not available")

        try:
            client_id = uuid.UUID(input_data["client_id"])
            client = await client_service.get_client(client_id, context.user)
            if not client:
                return ToolResult.fail("NOT_FOUND", f"Client {client_id} not found")
            return ToolResult.ok(client.model_dump(mode="json"))
        except ValueError as e:
            return ToolResult.fail("VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.exception("client.get failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to get client: {e}")


class ClientListTool(AgentTool):
    """List clients."""

    @property
    def name(self) -> str:
        return "client.list"

    @property
    def description(self) -> str:
        return "List and search clients with an optional search query."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search query for client name/company/email"},
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
        client_service = context.extra.get("client_service")
        if not client_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Client service not available")

        try:
            limit = input_data.pop("limit", 20)
            items, total = await client_service.list_clients(
                user=context.user,
                skip=0,
                limit=limit,
                **input_data,
            )
            return ToolResult.ok(
                {
                    "clients": [c.model_dump(mode="json") for c in items],
                    "total": total,
                    "returned": len(items),
                }
            )
        except Exception as e:
            logger.exception("client.list failed")
            return ToolResult.fail("INTERNAL_ERROR", f"Failed to list clients: {e}")


def get_client_tools() -> list[AgentTool]:
    """Return all client tools for registry registration."""
    return [ClientGetTool(), ClientListTool()]
