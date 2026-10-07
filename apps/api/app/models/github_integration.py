"""GitHub integration model for secure credential storage."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, UniqueConstraint
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

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    github_user_id: Mapped[Optional[int]] = mapped_column()  # GitHub's numeric user ID
    username: Mapped[Optional[str]] = mapped_column(String(255))
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[Optional[str]] = mapped_column(String(500))  # Comma-separated scopes
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User")
