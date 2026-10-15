"""Add proposals and proposal_versions tables

Revision ID: 009_proposals
Revises: 008_google_integrations
Create Date: 2026-10-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_proposals"
down_revision: str | None = "008_google_integrations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "analysis_id",
            sa.String(36),
            sa.ForeignKey("requirements_analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("client_name", sa.String(255), nullable=True),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("line_items", sa.JSON, nullable=True),
        sa.Column("sections", sa.JSON, nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("subtotal", sa.Float, nullable=True),
        sa.Column("discount_percent", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("tax_percent", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_amount", sa.Float, nullable=True),
        sa.Column("valid_until", sa.String(30), nullable=True),
        sa.Column("estimated_duration_weeks", sa.Integer, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
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
    op.create_index("ix_proposals_project_id", "proposals", ["project_id"])
    op.create_index("ix_proposals_user_id", "proposals", ["user_id"])
    op.create_index("ix_proposals_status", "proposals", ["status"])
    op.create_index("ix_proposals_analysis_id", "proposals", ["analysis_id"])

    op.create_table(
        "proposal_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "proposal_id", sa.String(36), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("snapshot", sa.JSON, nullable=False),
        sa.Column("change_note", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("proposal_id", "version_number", name="uq_proposal_version"),
    )
    op.create_index("ix_proposal_versions_proposal_id", "proposal_versions", ["proposal_id"])


def downgrade() -> None:
    op.drop_table("proposal_versions")
    op.drop_table("proposals")

