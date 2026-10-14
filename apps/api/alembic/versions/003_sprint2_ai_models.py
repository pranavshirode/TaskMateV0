"""sprint2_ai_models

Revision ID: 003_sprint2
Revises: 002_sprint1
Create Date: 2024-01-03 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_sprint2'
down_revision: str | None = '002_sprint1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # Conversation messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('raw_entities', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_conversation_messages_conversation_id', 'conversation_messages', ['conversation_id'])

    # AI Request Logs table
    op.create_table(
        'ai_request_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='SUCCESS'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_request_logs_user_id', 'ai_request_logs', ['user_id'])
    op.create_index('ix_ai_request_logs_conversation_id', 'ai_request_logs', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('ai_request_logs')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')

