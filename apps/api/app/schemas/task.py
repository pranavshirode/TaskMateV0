from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.task_label import TaskLabelResponse

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    project_id: str | None = None
    client_id: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    estimated_minutes: int | None = Field(None, ge=0)
    labels: list[str] | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    project_id: str | None = None
    client_id: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    estimated_minutes: int | None = Field(None, ge=0)
    labels: list[str] | None = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskPriorityUpdate(BaseModel):
    priority: TaskPriority

class TaskResponse(BaseModel):
    id: str
    user_id: str
    project_id: str | None
    client_id: str | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    estimated_minutes: int | None
    actual_minutes: int | None
    source: str | None
    external_reference: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
    labels: list[TaskLabelResponse]
    
    model_config = ConfigDict(from_attributes=True)

class TaskListResponse(BaseModel):
    id: str
    user_id: str
    project_id: str | None
    client_id: str | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    estimated_minutes: int | None
    actual_minutes: int | None
    source: str | None
    external_reference: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
    labels: list[TaskLabelResponse]
    
    model_config = ConfigDict(from_attributes=True)
