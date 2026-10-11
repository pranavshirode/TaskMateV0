"""GitHub integration model for secure credential storage."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GitHubIntegration(Base):
    """Stores a user's GitHub connection.

    Access tokens are encrypted at rest using Fernet.
    Tokens are NEVER sent to the LLM or exposed via API.
    """

    __tablename__ = "github_integrations"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_github_integration_user"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_user_id: Mapped[int | None] = mapped_column(nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User")
