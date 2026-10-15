"""Client communication and follow-up tracking models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.project import Project
    from app.models.user import User


class ClientCommunication(Base):
    """Tracks drafted, approved, and sent communications with a client.

    Lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED -> SENT (or CANCELLED)
    Approval-controlled: Cannot be dispatched without approval.
    """

    __tablename__ = "client_communications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="EMAIL", nullable=False)  # EMAIL, SLACK, WHATSAPP, NOTE
    communication_type: Mapped[str] = mapped_column(
        String(50), default="FOLLOW_UP", nullable=False
    )  # FOLLOW_UP, STATUS_UPDATE, MILESTONE_DELIVERY, PROPOSAL_OUTREACH, CHECK_IN

    status: Mapped[str] = mapped_column(
        String(30), default="DRAFT", nullable=False, index=True
    )  # DRAFT, PENDING_APPROVAL, APPROVED, SENT, CANCELLED

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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

    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="communications", lazy="selectin")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="selectin")
