"""API endpoints for Client Requests and Change Impact Analysis."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_client_request_service
from app.models.user import User
from app.schemas.requirements import (
    ClientRequestCreate,
    ClientRequestImpactResponse,
    ClientRequestResponse,
)
from app.services.client_request import ClientRequestService

router = APIRouter()


@router.get("/projects/{project_id}/client-requests", response_model=list[ClientRequestResponse])
async def list_project_client_requests(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientRequestService = Depends(get_client_request_service),
):
    return await service.list_requests(str(current_user.id), project_id)


@router.post("/projects/{project_id}/client-requests", response_model=ClientRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_client_request(
    project_id: str,
    data: ClientRequestCreate,
    current_user: User = Depends(get_current_user),
    service: ClientRequestService = Depends(get_client_request_service),
):
    return await service.create_request(str(current_user.id), project_id, data)


@router.get("/client-requests/{request_id}", response_model=ClientRequestResponse)
async def get_client_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientRequestService = Depends(get_client_request_service),
):
    return await service.get_request(str(current_user.id), request_id)


@router.post("/client-requests/{request_id}/analyze-impact", response_model=ClientRequestImpactResponse)
async def analyze_client_request_impact(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientRequestService = Depends(get_client_request_service),
):
    return await service.analyze_impact(str(current_user.id), request_id)


@router.post("/client-requests/{request_id}/approve", response_model=ClientRequestResponse)
async def approve_client_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ClientRequestService = Depends(get_client_request_service),
):
    return await service.approve_request(str(current_user.id), request_id)

