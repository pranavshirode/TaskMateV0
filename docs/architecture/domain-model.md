# TaskMate AI — Domain Model

## Overview

TaskMate AI is an agentic AI workspace for developer freelancers. Sprint 1 establishes the core structured data layer that the AI agent (Sprint 2) will operate on.

## Entity Relationship Diagram

```
User
 │
 ├── Client (1:N)
 │       │
 │       └── Project (1:N)
 │              │
 │              ├── Repository (1:N)
 │              │
 │              └── Task (1:N)
 │                    │
 │                    ├── TaskLabel (M:N via task_label_associations)
 │                    └── TaskEvent (1:N)
 │
 └── Task (1:N, direct ownership)
```

## Entities

### User
The developer freelancer using the system.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| name | String(255) | NOT NULL |
| email | String(255) | NOT NULL, UNIQUE |
| password_hash | String(255) | NOT NULL |
| is_active | Boolean | NOT NULL, DEFAULT true |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |

### Client
A freelancing client the developer works with.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| user_id | UUID | FK → users.id, NOT NULL |
| name | String(255) | NOT NULL |
| company_name | String(255) | NULLABLE |
| email | String(255) | NULLABLE |
| phone | String(50) | NULLABLE |
| notes | Text | NULLABLE |
| status | Enum(ACTIVE, ARCHIVED) | NOT NULL |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |
| archived_at | DateTime(tz) | NULLABLE |

### Project
A development project for a client.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| user_id | UUID | FK → users.id, NOT NULL |
| client_id | UUID | FK → clients.id, NULLABLE |
| name | String(255) | NOT NULL |
| description | Text | NULLABLE |
| status | Enum(PLANNING, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED) | NOT NULL |
| start_date | Date | NULLABLE |
| deadline | Date | NULLABLE |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |
| archived_at | DateTime(tz) | NULLABLE |

### Repository
A development code repository linked to a project.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| project_id | UUID | FK → projects.id, NOT NULL |
| name | String(255) | NOT NULL |
| provider | Enum(GITHUB, GITLAB, BITBUCKET) | NOT NULL |
| url | String(1024) | NOT NULL |
| default_branch | String(255) | NOT NULL |
| description | Text | NULLABLE |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |

### Task
The central work unit.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| user_id | UUID | FK → users.id, NOT NULL |
| project_id | UUID | FK → projects.id, NULLABLE |
| client_id | UUID | FK → clients.id, NULLABLE |
| title | String(500) | NOT NULL |
| description | Text | NULLABLE |
| status | Enum(BACKLOG, TODO, IN_PROGRESS, BLOCKED, REVIEW, COMPLETED) | NOT NULL |
| priority | Enum(LOW, MEDIUM, HIGH, URGENT) | NOT NULL |
| due_date | Date | NULLABLE |
| estimated_minutes | Integer | NULLABLE |
| actual_minutes | Integer | NULLABLE |
| source | String(255) | NULLABLE |
| external_reference | String(255) | NULLABLE |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |
| completed_at | DateTime(tz) | NULLABLE |
| archived_at | DateTime(tz) | NULLABLE |

### TaskLabel
Lightweight tags for task categorization.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| user_id | UUID | FK → users.id, NOT NULL |
| name | String(100) | NOT NULL |
| color | String(7) | NULLABLE |
| created_at | DateTime(tz) | NOT NULL |

### TaskEvent
Activity log for task changes.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID (String 36) | Primary Key |
| task_id | UUID | FK → tasks.id, NOT NULL |
| user_id | UUID | FK → users.id, NOT NULL |
| event_type | Enum(TASK_CREATED, TASK_UPDATED, STATUS_CHANGED, PRIORITY_CHANGED, DUE_DATE_CHANGED, TASK_COMPLETED, TASK_ARCHIVED) | NOT NULL |
| old_value | String(1024) | NULLABLE |
| new_value | String(1024) | NULLABLE |
| created_at | DateTime(tz) | NOT NULL |

## Data Isolation

Every query is scoped by `user_id`. A user can only access their own data. This is enforced at the service layer.

## Cascade Behavior

- User → Client: CASCADE (deleting user deletes clients)
- Client → Project: SET NULL (archiving client preserves projects)
- Project → Repository: CASCADE (deleting project removes repos)
- Project → Task: SET NULL (archiving project preserves tasks)
- Task → TaskLabel: CASCADE (via association table)
- Task → TaskEvent: CASCADE (deleting task removes events)
