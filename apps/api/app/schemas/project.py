import uuid
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None

class ProjectCreate(ProjectBase):
    client_id: Optional[uuid.UUID] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None

class ProjectInDBBase(ProjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class Project(ProjectInDBBase):
    pass

class ProjectListResponse(BaseModel):
    items: list[Project]
    page: int
    page_size: int
    total: int
