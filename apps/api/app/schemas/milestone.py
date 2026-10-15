"""Pydantic schemas for milestones and task dependencies."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = "OPEN"
    due_date: Optional[date] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None


class MilestoneResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    task_count: int = 0
    completed_task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskDependencyCreate(BaseModel):
    depends_on_task_id: str


class TaskDependencyResponse(BaseModel):
    id: str
    task_id: str
    depends_on_task_id: str
    depends_on_title: Optional[str] = None
    depends_on_status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

