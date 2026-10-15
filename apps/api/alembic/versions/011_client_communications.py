"""Add client_communications table

Revision ID: 011_client_comms
Revises: 010_milestones_deps
Create Date: 2026-10-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011_client_comms"
down_revision: str | None = "010_milestones_deps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_communications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("client_id", sa.String(36), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("channel", sa.String(50), nullable=False, server_default="EMAIL"),
        sa.Column("communication_type", sa.String(50), nullable=False, server_default="FOLLOW_UP"),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_client_comms_client_id", "client_communications", ["client_id"])
    op.create_index("ix_client_comms_project_id", "client_communications", ["project_id"])
    op.create_index("ix_client_comms_user_id", "client_communications", ["user_id"])
    op.create_index("ix_client_comms_status", "client_communications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_client_comms_status", "client_communications")
    op.drop_index("ix_client_comms_user_id", "client_communications")
    op.drop_index("ix_client_comms_project_id", "client_communications")
    op.drop_index("ix_client_comms_client_id", "client_communications")
    op.drop_table("client_communications")

