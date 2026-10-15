"""Pydantic schemas for proposals and quotations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    total: Optional[float] = None

    @model_validator(mode="after")
    def compute_total(self) -> "LineItem":
        if self.total is None:
            self.total = round(self.quantity * self.unit_price, 2)
        return self


class ProposalSection(BaseModel):
    heading: str
    content: str


class ProposalCreate(BaseModel):
    project_id: str
    analysis_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=255)
    client_name: Optional[str] = None
    executive_summary: Optional[str] = None
    line_items: list[LineItem] = Field(default_factory=list)
    sections: list[ProposalSection] = Field(default_factory=list)
    currency: str = "USD"
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    tax_percent: float = Field(default=0.0, ge=0, le=100)
    valid_until: Optional[str] = None  # ISO date string e.g. "2026-11-30"
    estimated_duration_weeks: Optional[int] = None
    notes: Optional[str] = None


class ProposalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    client_name: Optional[str] = None
    executive_summary: Optional[str] = None
    line_items: Optional[list[LineItem]] = None
    sections: Optional[list[ProposalSection]] = None
    currency: Optional[str] = None
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    tax_percent: Optional[float] = Field(None, ge=0, le=100)
    valid_until: Optional[str] = None
    estimated_duration_weeks: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # Only DRAFT → PENDING_APPROVAL transition is user-driven here


class ProposalVersionSummary(BaseModel):
    id: str
    version_number: int
    change_note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProposalResponse(BaseModel):
    id: str
    project_id: str
    analysis_id: Optional[str] = None
    user_id: str
    title: str
    client_name: Optional[str] = None
    executive_summary: Optional[str] = None
    line_items: list[Any] = Field(default_factory=list)
    sections: list[Any] = Field(default_factory=list)
    currency: str = "USD"
    subtotal: Optional[float] = None
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    total_amount: Optional[float] = None
    valid_until: Optional[str] = None
    estimated_duration_weeks: Optional[int] = None
    status: str
    version: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version_history: list[ProposalVersionSummary] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProposalStatusTransition(BaseModel):
    status: str  # e.g. "SENT", "ACCEPTED", "REJECTED"
    note: Optional[str] = None


class AIGenerateProposalRequest(BaseModel):
    """Request body for AI-assisted proposal generation."""
    project_id: str
    analysis_id: str
    additional_notes: Optional[str] = None

