from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    client_id: str | None = None
    description: str | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    deadline: date | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    client_id: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    deadline: date | None = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    client_id: str | None
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    deadline: date | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    task_summary: dict[str, int]
