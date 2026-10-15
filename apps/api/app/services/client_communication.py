"""Client communication and follow-up service.

Handles drafting, scheduling, approval gating, and status transitions for client outreach.
Enforces the safety invariant: No message can be dispatched/sent without prior explicit approval.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.providers.base import AIMessage, BaseAIProvider
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.client import Client
from app.models.client_communication import ClientCommunication
from app.models.project import Project
from app.schemas.client_communication import (
    AIGenerateCommunicationRequest,
    ClientCommunicationCreate,
    ClientCommunicationUpdate,
)

logger = logging.getLogger(__name__)

# Valid state transitions for communication lifecycle
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"PENDING_APPROVAL", "CANCELLED"},
    "PENDING_APPROVAL": {"APPROVED", "DRAFT", "CANCELLED"},
    "APPROVED": {"SENT", "CANCELLED", "DRAFT"},
    "SENT": set(),  # terminal state
    "CANCELLED": {"DRAFT"},  # can revive as draft
}


class ClientCommunicationService:
    """Business logic for client communications and follow-ups."""

    def __init__(self, db: AsyncSession, ai_provider: BaseAIProvider | None = None) -> None:
        self.db = db
        self.ai_provider = ai_provider

    async def _verify_client_owner(self, user_id: str, client_id: str) -> Client:
        stmt = select(Client).where(Client.id == client_id, Client.user_id == user_id)
        result = await self.db.execute(stmt)
        client = result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client not found")
        return client

    async def _verify_project_owner(self, user_id: str, project_id: str) -> Project:
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project not found")
        return project

    async def create_communication(
        self, user_id: str, data: ClientCommunicationCreate
    ) -> ClientCommunication:
        """Create a new client communication draft."""
        await self._verify_client_owner(user_id, data.client_id)

        if data.project_id:
            await self._verify_project_owner(user_id, data.project_id)

        comm = ClientCommunication(
            client_id=data.client_id,
            project_id=data.project_id,
            user_id=user_id,
            subject=data.subject,
            content=data.content,
            channel=data.channel or "EMAIL",
            communication_type=data.communication_type or "FOLLOW_UP",
            status="DRAFT",
            scheduled_at=data.scheduled_at,
            notes=data.notes,
        )
        self.db.add(comm)
        await self.db.commit()
        await self.db.refresh(comm, attribute_names=["client", "project"])
        return comm

    async def list_communications(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[ClientCommunication]:
        """List communications scoped to the current user, with optional filters."""
        stmt = (
            select(ClientCommunication)
            .options(selectinload(ClientCommunication.client), selectinload(ClientCommunication.project))
            .where(ClientCommunication.user_id == user_id)
        )
        if client_id:
            stmt = stmt.where(ClientCommunication.client_id == client_id)
        if project_id:
            stmt = stmt.where(ClientCommunication.project_id == project_id)
        if status:
            stmt = stmt.where(ClientCommunication.status == status)

        stmt = stmt.order_by(desc(ClientCommunication.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_communication(self, user_id: str, comm_id: str) -> ClientCommunication:
        """Get a single communication by ID."""
        stmt = (
            select(ClientCommunication)
            .options(selectinload(ClientCommunication.client), selectinload(ClientCommunication.project))
            .where(ClientCommunication.id == comm_id, ClientCommunication.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        comm = result.scalar_one_or_none()
        if not comm:
            raise NotFoundError("Client communication not found")
        return comm

    async def update_communication(
        self, user_id: str, comm_id: str, data: ClientCommunicationUpdate
    ) -> ClientCommunication:
        """Update an existing communication."""
        comm = await self.get_communication(user_id, comm_id)

        if comm.status == "SENT":
            raise ValidationError("Cannot modify a communication that has already been sent.")

        if data.subject is not None:
            comm.subject = data.subject
        if data.content is not None:
            comm.content = data.content
        if data.channel is not None:
            comm.channel = data.channel
        if data.communication_type is not None:
            comm.communication_type = data.communication_type
        if data.scheduled_at is not None:
            comm.scheduled_at = data.scheduled_at
        if data.notes is not None:
            comm.notes = data.notes
        if data.status is not None and data.status != comm.status:
            return await self.transition_status(user_id, comm_id, data.status, notes=data.notes)

        await self.db.commit()
        await self.db.refresh(comm, attribute_names=["client", "project"])
        return comm

    async def transition_status(
        self, user_id: str, comm_id: str, target_status: str, notes: Optional[str] = None
    ) -> ClientCommunication:
        """Transition communication lifecycle status with strict approval enforcement.

        Invariant: Cannot send without being in APPROVED status.
        """
        comm = await self.get_communication(user_id, comm_id)
        target = target_status.upper()

        if target == "SENT" and comm.status != "APPROVED":
            raise ValidationError(
                "Communication must be APPROVED by the user before it can be sent.",
                code="APPROVAL_REQUIRED",
            )

        allowed = _ALLOWED_TRANSITIONS.get(comm.status, set())
        if target not in allowed:
            raise ValidationError(
                f"Cannot transition communication from '{comm.status}' to '{target}'. Allowed: {sorted(allowed)}",
                code="INVALID_STATUS_TRANSITION",
            )

        now = datetime.now(timezone.utc)
        if target == "APPROVED":
            comm.approved_at = now
        elif target == "SENT":
            comm.sent_at = now

        comm.status = target
        if notes:
            comm.notes = f"{comm.notes}\n{notes}".strip() if comm.notes else notes

        await self.db.commit()
        await self.db.refresh(comm, attribute_names=["client", "project"])
        return comm

    async def delete_communication(self, user_id: str, comm_id: str) -> None:
        """Delete an unsent communication."""
        comm = await self.get_communication(user_id, comm_id)
        if comm.status == "SENT":
            raise ValidationError(
                "Cannot delete an audit-logged sent communication.",
                code="CANNOT_DELETE_SENT",
            )
        await self.db.delete(comm)
        await self.db.commit()

    async def ai_generate_draft(
        self, user_id: str, request: AIGenerateCommunicationRequest
    ) -> ClientCommunication:
        """Use AI to draft an outreach or follow-up communication based on client/project context."""
        if self.ai_provider is None:
            raise ConflictError("AI provider not configured.", code="AI_UNAVAILABLE")

        client = await self._verify_client_owner(user_id, request.client_id)
        project: Optional[Project] = None
        if request.project_id:
            project = await self._verify_project_owner(user_id, request.project_id)

        prompt = f"""You are a professional software consultant and developer drafting a message to a client.

Client Name: {client.name}
Company: {client.company_name or 'Independent'}
Project: {project.name if project else 'General client engagement'}
Project Status: {project.status.value if project and hasattr(project.status, 'value') else (project.status if project else 'N/A')}
Communication Type: {request.communication_type}
Desired Tone: {request.tone}
Context/Instructions: {request.context_notes or 'Standard check-in on project status, progress, and next steps.'}

Draft a clear, polite, and actionable communication message.
Respond with a JSON object in this format:
{{
  "subject": "Clear and relevant subject line",
  "content": "Complete draft of the message body, formatted with appropriate paragraphs."
}}
Respond with ONLY valid JSON."""

        try:
            response = await self.ai_provider.generate(
                [AIMessage(role="user", content=prompt)],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500,
            )
            parsed = json.loads(response.content)
        except Exception as e:
            logger.warning("AI draft generation failed: %s", e)
            raise ConflictError(
                "AI could not generate draft communication. Please draft manually.",
                code="AI_GENERATION_FAILED",
            ) from e

        create_data = ClientCommunicationCreate(
            client_id=client.id,
            project_id=project.id if project else None,
            subject=parsed.get("subject", f"Update regarding {project.name if project else 'our collaboration'}"),
            content=parsed.get("content", ""),
            channel="EMAIL",
            communication_type=request.communication_type,
            notes=f"AI drafted ({request.tone} tone)",
        )
        return await self.create_communication(user_id, create_data)

