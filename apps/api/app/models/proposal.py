"""Proposal model — client-facing project proposals generated from requirements analyses."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Proposal(Base):
    """A versioned client proposal derived from a requirements analysis.

    Lifecycle: DRAFT → PENDING_APPROVAL → SENT → ACCEPTED | REJECTED
    """

    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("requirements_analyses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON-stored line items: [{description, quantity, unit_price, total}]
    line_items: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    # JSON-stored sections: [{heading, content}]
    sections: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)

    # Pricing
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    subtotal: Mapped[Optional[float]] = mapped_column(nullable=True)
    discount_percent: Mapped[float] = mapped_column(default=0.0, nullable=False)
    tax_percent: Mapped[float] = mapped_column(default=0.0, nullable=False)
    total_amount: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Validity
    valid_until: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # ISO date string
    estimated_duration_weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="DRAFT", index=True
    )  # DRAFT, PENDING_APPROVAL, SENT, ACCEPTED, REJECTED
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    versions: Mapped[list["ProposalVersion"]] = relationship(
        "ProposalVersion", back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )


class ProposalVersion(Base):
    """Immutable snapshot of a proposal at a given version number."""

    __tablename__ = "proposal_versions"
    __table_args__ = (UniqueConstraint("proposal_id", "version_number", name="uq_proposal_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)  # Full proposal data at this version
    change_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="versions")

