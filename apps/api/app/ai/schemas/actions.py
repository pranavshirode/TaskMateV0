"""Action schemas for validated, resolved AI actions ready for execution."""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel, Field


class ActionType(str, enum.Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    CHANGE_TASK_STATUS = "CHANGE_TASK_STATUS"
    CHANGE_TASK_PRIORITY = "CHANGE_TASK_PRIORITY"
    SEARCH_TASKS = "SEARCH_TASKS"
    GET_TODAY_DASHBOARD = "GET_TODAY_DASHBOARD"
    GET_OVERDUE_TASKS = "GET_OVERDUE_TASKS"
    GET_PROJECT_INFO = "GET_PROJECT_INFO"
    GET_CLIENT_INFO = "GET_CLIENT_INFO"
    RESPOND = "RESPOND"  # Just answer with text, no mutation
    CLARIFY = "CLARIFY"  # Ask user for clarification


class CreateTaskAction(BaseModel):
    title: str
    description: str | None = None
    project_id: str | None = None
    client_id: str | None = None
    priority: str = "MEDIUM"
    status: str = "TODO"
    due_date: date | None = None
    labels: list[str] = Field(default_factory=list)
    estimated_minutes: int | None = None


class UpdateTaskAction(BaseModel):
    task_id: str
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None


class ChangeTaskStatusAction(BaseModel):
    task_id: str
    status: str


class ChangeTaskPriorityAction(BaseModel):
    task_id: str
    priority: str


class SearchTasksAction(BaseModel):
    search: str | None = None
    status: str | None = None
    priority: str | None = None
    project_id: str | None = None
    client_id: str | None = None


class GetProjectInfoAction(BaseModel):
    project_id: str


class GetClientInfoAction(BaseModel):
    client_id: str


class ResolvedAction(BaseModel):
    """An action that has been validated and resolved against the database."""

    type: ActionType
    parameters: dict = Field(default_factory=dict)
