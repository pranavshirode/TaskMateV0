"""Per-user Google account connections (encrypted OAuth tokens) for Google Workspace MCP tools.

Revision ID: 008_google_integrations
Revises: 007_requirement_source
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_google_integrations"
down_revision: str | None = "007_requirement_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "google_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_email", sa.String(255), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_google_integration_user"),
    )
    op.create_index("ix_google_integrations_user_id", "google_integrations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_google_integrations_user_id", table_name="google_integrations")
    op.drop_table("google_integrations")
