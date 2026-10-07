from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.schemas.task import Task
from app.schemas.project import Project

class DashboardTodayResponse(BaseModel):
    date: date
    due_today: List[Task]
    overdue: List[Task]
    high_priority: List[Task]
    recently_updated: List[Task]
    active_projects: List[Project]
