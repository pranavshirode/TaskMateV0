"""Client communication and follow-up API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_ai_provider
from app.api.deps import get_current_user, get_db
from app.models.client_communication import ClientCommunication
from app.models.user import User
from app.schemas.client_communication import (
    AIGenerateCommunicationRequest,
    ClientCommunicationCreate,
    ClientCommunicationResponse,
    ClientCommunicationStatusUpdate,
    ClientCommunicationUpdate,
)
from app.services.client_communication import ClientCommunicationService

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> ClientCommunicationService:
    ai_provider = get_ai_provider()
    return ClientCommunicationService(db, ai_provider=ai_provider)


def _to_response(c: ClientCommunication) -> ClientCommunicationResponse:
    client_name = c.client.name if getattr(c, "client", None) else None
    project_name = c.project.name if getattr(c, "project", None) else None
    return ClientCommunicationResponse(
        id=c.id,
        client_id=c.client_id,
        project_id=c.project_id,
        user_id=c.user_id,
        subject=c.subject,
        content=c.content,
        channel=c.channel,
        communication_type=c.communication_type,
        status=c.status,
        scheduled_at=c.scheduled_at,
        approved_at=c.approved_at,
        sent_at=c.sent_at,
        notes=c.notes,
        client_name=client_name,
        project_name=project_name,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post(
    "/client-communications",
    response_model=ClientCommunicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_communication(
    data: ClientCommunicationCreate,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Create a new client communication draft."""
    comm = await service.create_communication(str(current_user.id), data)
    return _to_response(comm)


@router.get(
    "/client-communications",
    response_model=list[ClientCommunicationResponse],
)
async def list_communications(
    client_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> list[ClientCommunicationResponse]:
    """List client communications with optional filters."""
    comms = await service.list_communications(
        str(current_user.id), client_id=client_id, project_id=project_id, status=status
    )
    return [_to_response(c) for c in comms]


@router.get(
    "/clients/{client_id}/communications",
    response_model=list[ClientCommunicationResponse],
)
async def list_client_communications(
    client_id: str,
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> list[ClientCommunicationResponse]:
    """List all communications for a specific client."""
    comms = await service.list_communications(
        str(current_user.id), client_id=client_id, project_id=project_id, status=status
    )
    return [_to_response(c) for c in comms]


@router.get(
    "/client-communications/{communication_id}",
    response_model=ClientCommunicationResponse,
)
async def get_communication(
    communication_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Get a single communication by ID."""
    comm = await service.get_communication(str(current_user.id), communication_id)
    return _to_response(comm)


@router.patch(
    "/client-communications/{communication_id}",
    response_model=ClientCommunicationResponse,
)
async def update_communication(
    communication_id: str,
    data: ClientCommunicationUpdate,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Update fields on an unsent communication."""
    comm = await service.update_communication(str(current_user.id), communication_id, data)
    return _to_response(comm)


@router.post(
    "/client-communications/{communication_id}/approve",
    response_model=ClientCommunicationResponse,
)
async def approve_communication(
    communication_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Approve a communication for sending."""
    comm = await service.transition_status(
        str(current_user.id), communication_id, "APPROVED", notes="Approved by user"
    )
    return _to_response(comm)


@router.post(
    "/client-communications/{communication_id}/send",
    response_model=ClientCommunicationResponse,
)
async def send_communication(
    communication_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Dispatch/mark an approved communication as SENT."""
    comm = await service.transition_status(
        str(current_user.id), communication_id, "SENT", notes="Dispatched to client"
    )
    return _to_response(comm)


@router.post(
    "/client-communications/{communication_id}/status",
    response_model=ClientCommunicationResponse,
)
async def transition_communication_status(
    communication_id: str,
    data: ClientCommunicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Transition communication lifecycle status."""
    comm = await service.transition_status(
        str(current_user.id), communication_id, data.status, notes=data.notes
    )
    return _to_response(comm)


@router.delete(
    "/client-communications/{communication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_communication(
    communication_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> None:
    """Delete an unsent communication."""
    await service.delete_communication(str(current_user.id), communication_id)


@router.post(
    "/client-communications/ai-draft",
    response_model=ClientCommunicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ai_draft_communication(
    data: AIGenerateCommunicationRequest,
    current_user: User = Depends(get_current_user),
    service: ClientCommunicationService = Depends(_get_service),
) -> ClientCommunicationResponse:
    """Use AI to draft a communication based on client/project context."""
    comm = await service.ai_generate_draft(str(current_user.id), data)
    return _to_response(comm)

