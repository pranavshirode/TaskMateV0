"""API endpoints for Project Context Notes and Explicit Memory."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_project_context_service
from app.models.user import User
from app.schemas.requirements import (
    ProjectContextNoteCreate,
    ProjectContextNoteResponse,
    ProjectContextNoteUpdate,
)
from app.services.project_context import ProjectContextService

router = APIRouter()


@router.get("/projects/{project_id}/context", response_model=list[ProjectContextNoteResponse])
async def list_project_context_notes(
    project_id: str,
    include_superseded: bool = False,
    current_user: User = Depends(get_current_user),
    service: ProjectContextService = Depends(get_project_context_service),
):
    notes = await service.list_notes(str(current_user.id), project_id, include_superseded=include_superseded)
    return notes


@router.post("/projects/{project_id}/context", response_model=ProjectContextNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_project_context_note(
    project_id: str,
    data: ProjectContextNoteCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectContextService = Depends(get_project_context_service),
):
    note = await service.create_note(str(current_user.id), project_id, data)
    return note


@router.get("/context/{note_id}", response_model=ProjectContextNoteResponse)
async def get_context_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    service: ProjectContextService = Depends(get_project_context_service),
):
    return await service.get_note(str(current_user.id), note_id)


@router.put("/context/{note_id}", response_model=ProjectContextNoteResponse)
async def update_context_note(
    note_id: str,
    data: ProjectContextNoteUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectContextService = Depends(get_project_context_service),
):
    return await service.update_note(str(current_user.id), note_id, data)


@router.delete("/context/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_context_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    service: ProjectContextService = Depends(get_project_context_service),
):
    await service.delete_note(str(current_user.id), note_id)

