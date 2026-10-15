"""Proposal tools for the agent system.

Enables the AI agent to draft and inspect proposals and quotes.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult
from app.schemas.proposal import ProposalCreate

logger = logging.getLogger(__name__)


class ProposalCreateTool(AgentTool):
    """Create a new proposal draft for a project."""

    @property
    def name(self) -> str:
        return "proposal.create"

    @property
    def description(self) -> str:
        return (
            "Create a new proposal draft for a project. Requires project_id and title. "
            "Optionally client_name, executive_summary, currency, and line_items."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "title": {"type": "string", "description": "Proposal title"},
                "client_name": {"type": "string", "description": "Client name"},
                "executive_summary": {"type": "string", "description": "Executive summary"},
                "currency": {"type": "string", "default": "USD", "description": "Currency code (e.g. USD, EUR)"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number", "default": 1},
                            "unit_price": {"type": "number"},
                        },
                        "required": ["description", "unit_price"],
                    },
                    "description": "List of deliverables and pricing",
                },
            },
            "required": ["project_id", "title"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.WRITE

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        proposal_service = context.extra.get("proposal_service")
        if not proposal_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Proposal service not available")

        try:
            data = ProposalCreate(**input_data)
            proposal = await proposal_service.create_proposal(str(context.user.id), data)
            return ToolResult.ok({
                "id": proposal.id,
                "project_id": proposal.project_id,
                "title": proposal.title,
                "status": proposal.status,
                "version": proposal.version,
                "subtotal": proposal.subtotal,
                "total_amount": proposal.total_amount,
                "currency": proposal.currency,
            })
        except Exception as e:
            logger.error("Failed to create proposal: %s", e)
            return ToolResult.fail("EXECUTION_ERROR", str(e))


class ProposalListTool(AgentTool):
    """List proposals for a project."""

    @property
    def name(self) -> str:
        return "proposal.list"

    @property
    def description(self) -> str:
        return "List all proposals for a project by project_id."

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
        proposal_service = context.extra.get("proposal_service")
        if not proposal_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "Proposal service not available")

        try:
            proposals = await proposal_service.list_proposals(str(context.user.id), input_data["project_id"])
            return ToolResult.ok({
                "proposals": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "status": p.status,
                        "version": p.version,
                        "total_amount": p.total_amount,
                        "currency": p.currency,
                    }
                    for p in proposals
                ]
            })
        except Exception as e:
            logger.error("Failed to list proposals: %s", e)
            return ToolResult.fail("EXECUTION_ERROR", str(e))


def get_proposal_tools() -> list[AgentTool]:
    return [ProposalCreateTool(), ProposalListTool()]

