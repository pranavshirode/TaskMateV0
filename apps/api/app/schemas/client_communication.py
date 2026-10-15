"""Pydantic schemas for client communications and follow-ups."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClientCommunicationCreate(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    subject: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    channel: str = "EMAIL"  # EMAIL, SLACK, WHATSAPP, NOTE
    communication_type: str = "FOLLOW_UP"  # FOLLOW_UP, STATUS_UPDATE, MILESTONE_DELIVERY, PROPOSAL_OUTREACH, CHECK_IN
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None


class ClientCommunicationUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    channel: Optional[str] = None
    communication_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ClientCommunicationStatusUpdate(BaseModel):
    status: str  # DRAFT, PENDING_APPROVAL, APPROVED, SENT, CANCELLED
    notes: Optional[str] = None


class AIGenerateCommunicationRequest(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    communication_type: str = "FOLLOW_UP"
    tone: str = "professional"  # professional, friendly, urgent, concise
    context_notes: Optional[str] = None


class ClientCommunicationResponse(BaseModel):
    id: str
    client_id: str
    project_id: Optional[str] = None
    user_id: str
    subject: str
    content: str
    channel: str
    communication_type: str
    status: str
    scheduled_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    notes: Optional[str] = None
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

