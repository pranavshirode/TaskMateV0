"""sprint1_core_models

Revision ID: 002_sprint1
Revises: 1a2b3c4d5e6f
Create Date: 2024-01-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002_sprint1'
down_revision: str | None = '1a2b3c4d5e6f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Clients
    op.create_table(
        'clients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', name='clientstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_clients_user_id'), 'clients', ['user_id'], unique=False)
    op.create_index(op.f('ix_clients_status'), 'clients', ['status'], unique=False)

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(36), sa.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'ARCHIVED', name='projectstatus'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)
    op.create_index(op.f('ix_projects_client_id'), 'projects', ['client_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)

    # Repositories
    op.create_table(
        'repositories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('provider', sa.Enum('GITHUB', 'GITLAB', 'BITBUCKET', name='repositoryprovider'), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('default_branch', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_repositories_project_id'), 'repositories', ['project_id'], unique=False)

    # Tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('client_id', sa.String(36), sa.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('BACKLOG', 'TODO', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'COMPLETED', name='taskstatus'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='taskpriority'), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('actual_minutes', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('external_reference', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_tasks_client_id'), 'tasks', ['client_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)

    # Task Labels
    op.create_table(
        'task_labels',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_task_labels_user_id'), 'task_labels', ['user_id'], unique=False)

    # Task Label Associations
    op.create_table(
        'task_label_associations',
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('label_id', sa.String(36), sa.ForeignKey('task_labels.id', ondelete='CASCADE'), primary_key=True),
    )

    # Task Events
    op.create_table(
        'task_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.Enum('TASK_CREATED', 'TASK_UPDATED', 'STATUS_CHANGED', 'PRIORITY_CHANGED', 'DUE_DATE_CHANGED', 'TASK_COMPLETED', 'TASK_ARCHIVED', name='taskeventtype'), nullable=False),
        sa.Column('old_value', sa.String(1024), nullable=True),
        sa.Column('new_value', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_task_events_task_id'), 'task_events', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_events_user_id'), 'task_events', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('task_events')
    op.drop_table('task_label_associations')
    op.drop_table('task_labels')
    op.drop_table('tasks')
    op.drop_table('repositories')
    op.drop_table('projects')
    op.drop_table('clients')
    op.drop_table('users')
    
    # Drop enum types as well if necessary, but op.drop_table usually handles this in postgres
    sa.Enum(name='clientstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='projectstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='repositoryprovider').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskeventtype').drop(op.get_bind(), checkfirst=True)
