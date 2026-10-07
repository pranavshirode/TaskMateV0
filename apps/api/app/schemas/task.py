import uuid
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    source: Optional[str] = None
    external_reference: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None

class TaskStatusUpdate(BaseModel):
    status: str

class TaskPriorityUpdate(BaseModel):
    priority: str

class TaskInDBBase(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class Task(TaskInDBBase):
    pass

class TaskListResponse(BaseModel):
    items: list[Task]
    page: int
    page_size: int
    total: int

class TaskEventBase(BaseModel):
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

class TaskEvent(TaskEventBase):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
