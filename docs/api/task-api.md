# TaskMate AI — Task API Reference

Base URL: `/api/v1`

All endpoints require JWT Bearer token authentication unless noted.

## List Tasks

```http
GET /tasks
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| search | string | - | Search in title and description |
| status | TaskStatus | - | Filter by status |
| priority | TaskPriority | - | Filter by priority |
| project_id | UUID | - | Filter by project |
| client_id | UUID | - | Filter by client |
| due_date | date | - | Filter by due date (YYYY-MM-DD) |
| label | string | - | Filter by label name |
| archived | bool | false | Include archived tasks |
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| sort_by | string | created_at | Sort field: created_at, updated_at, due_date, title, priority |
| sort_order | string | desc | asc or desc |

**Response:** `PaginatedResponse[TaskResponse]`
```json
{
  "items": [TaskResponse],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

## Create Task

```http
POST /tasks
```

**Request Body:**
```json
{
  "title": "Build login page",
  "description": "Implement login with OAuth support",
  "project_id": "uuid",
  "client_id": "uuid",
  "status": "TODO",
  "priority": "HIGH",
  "due_date": "2024-03-15",
  "estimated_minutes": 120,
  "labels": ["frontend", "feature"]
}
```

Required: `title`
Defaults: `status=TODO`, `priority=MEDIUM`

**Response:** `201 Created` → `TaskResponse`

## Get Task

```http
GET /tasks/{task_id}
```

**Response:** `TaskResponse`

## Update Task

```http
PATCH /tasks/{task_id}
```

**Request Body:** Any subset of TaskCreate fields.

**Response:** `TaskResponse`

## Archive Task

```http
DELETE /tasks/{task_id}
```

Sets `archived_at` timestamp. Does not physically delete.

**Response:** `TaskResponse` (with archived_at set)

## Change Task Status

```http
PATCH /tasks/{task_id}/status
```

**Request Body:**
```json
{
  "status": "IN_PROGRESS"
}
```

Valid statuses: `BACKLOG`, `TODO`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `COMPLETED`

Records a `STATUS_CHANGED` event. Setting to `COMPLETED` sets `completed_at`.

**Response:** `TaskResponse`

## Change Task Priority

```http
PATCH /tasks/{task_id}/priority
```

**Request Body:**
```json
{
  "priority": "URGENT"
}
```

Valid priorities: `LOW`, `MEDIUM`, `HIGH`, `URGENT`

Records a `PRIORITY_CHANGED` event.

**Response:** `TaskResponse`

## List Task Events

```http
GET /tasks/{task_id}/events
```

**Query Parameters:** `page`, `page_size`

**Response:** `PaginatedResponse[TaskEventResponse]`

```json
{
  "items": [
    {
      "id": "uuid",
      "task_id": "uuid",
      "user_id": "uuid",
      "event_type": "STATUS_CHANGED",
      "old_value": "TODO",
      "new_value": "IN_PROGRESS",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 50
}
```

## TaskResponse Schema

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "project_id": "uuid | null",
  "client_id": "uuid | null",
  "title": "string",
  "description": "string | null",
  "status": "TaskStatus",
  "priority": "TaskPriority",
  "due_date": "date | null",
  "estimated_minutes": "int | null",
  "actual_minutes": "int | null",
  "source": "string | null",
  "external_reference": "string | null",
  "labels": [{"id": "uuid", "name": "string", "color": "#hex"}],
  "created_at": "datetime",
  "updated_at": "datetime",
  "completed_at": "datetime | null",
  "archived_at": "datetime | null"
}
```

## Enums

### TaskStatus
`BACKLOG` → `TODO` → `IN_PROGRESS` → `REVIEW` → `COMPLETED`

At any point: `→ BLOCKED → IN_PROGRESS`

Direct transitions like `TODO → COMPLETED` are allowed.

### TaskPriority
`LOW`, `MEDIUM`, `HIGH`, `URGENT`

### TaskEventType
`TASK_CREATED`, `TASK_UPDATED`, `STATUS_CHANGED`, `PRIORITY_CHANGED`, `DUE_DATE_CHANGED`, `TASK_COMPLETED`, `TASK_ARCHIVED`
