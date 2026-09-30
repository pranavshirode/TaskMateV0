from datetime import date
from pydantic import BaseModel
from app.schemas.task import TaskResponse
from app.schemas.project import ProjectResponse

class DashboardResponse(BaseModel):
    date: date
    due_today: list[TaskResponse]
    overdue: list[TaskResponse]
    high_priority: list[TaskResponse]
    active_projects: list[ProjectResponse]
    recently_updated: list[TaskResponse]
