"""Agent tools for client communication and follow-up management."""
from __future__ import annotations

from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult
from app.schemas.client_communication import ClientCommunicationCreate


class CommunicationCreateTool(AgentTool):
    """Tool for drafting a communication or follow-up for a client."""

    @property
    def name(self) -> str:
        return "client_communication.create"

    @property
    def description(self) -> str:
        return (
            "Create a client communication draft (email, follow-up, status update). "
            "Internal drafts are saved in DRAFT status and must be approved before sending."
        )

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "The client UUID"},
                "subject": {"type": "string", "description": "Subject line for the communication"},
                "content": {"type": "string", "description": "Body content of the message"},
                "channel": {
                    "type": "string",
                    "enum": ["EMAIL", "SLACK", "WHATSAPP", "NOTE"],
                    "default": "EMAIL",
                },
                "communication_type": {
                    "type": "string",
                    "enum": ["FOLLOW_UP", "STATUS_UPDATE", "MILESTONE_DELIVERY", "PROPOSAL_OUTREACH", "CHECK_IN"],
                    "default": "FOLLOW_UP",
                },
                "project_id": {"type": "string", "description": "Optional associated project UUID"},
                "notes": {"type": "string", "description": "Optional internal notes"},
            },
            "required": ["client_id", "subject", "content"],
        }

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        communication_service = context.extra.get("communication_service")
        if not communication_service:
            return ToolResult.fail("DEPENDENCY_MISSING", "Communication service not available in tool context")

        try:
            dto = ClientCommunicationCreate(
                client_id=input_data["client_id"],
                project_id=input_data.get("project_id"),
                subject=input_data["subject"],
                content=input_data["content"],
                channel=input_data.get("channel", "EMAIL"),
                communication_type=input_data.get("communication_type", "FOLLOW_UP"),
                notes=input_data.get("notes"),
            )
            comm = await communication_service.create_communication(str(context.user.id), dto)
            return ToolResult.ok({
                "id": str(comm.id),
                "client_id": str(comm.client_id),
                "subject": comm.subject,
                "status": comm.status,
                "channel": comm.channel,
                "message": "Draft created successfully. Awaiting review and approval.",
            })
        except Exception as e:
            return ToolResult.fail("CREATE_COMMUNICATION_ERROR", str(e))


class CommunicationListTool(AgentTool):
    """Tool for listing communications for a client."""

    @property
    def name(self) -> str:
        return "client_communication.list"

    @property
    def description(self) -> str:
        return "List communications and follow-ups for a specific client."

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "Filter by client UUID"},
                "project_id": {"type": "string", "description": "Filter by project UUID"},
                "status": {"type": "string", "description": "Filter by status: DRAFT, PENDING_APPROVAL, APPROVED, SENT"},
            },
        }

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        communication_service = context.extra.get("communication_service")
        if not communication_service:
            return ToolResult.fail("DEPENDENCY_MISSING", "Communication service not available in tool context")

        try:
            items = await communication_service.list_communications(
                str(context.user.id),
                client_id=input_data.get("client_id"),
                project_id=input_data.get("project_id"),
                status=input_data.get("status"),
            )
            return ToolResult.ok({
                "count": len(items),
                "communications": [
                    {
                        "id": str(c.id),
                        "client_id": str(c.client_id),
                        "subject": c.subject,
                        "status": c.status,
                        "channel": c.channel,
                        "communication_type": c.communication_type,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                    }
                    for c in items
                ],
            })
        except Exception as e:
            return ToolResult.fail("LIST_COMMUNICATIONS_ERROR", str(e))


def get_communication_tools() -> list[AgentTool]:
    return [CommunicationCreateTool(), CommunicationListTool()]

