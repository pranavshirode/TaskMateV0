"""Action schemas for AI-driven operations.

Actions represent validated, executable operations that the
AI orchestrator will perform via existing business services.
"""

import uuid
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.ai.schemas.intent import IntentType


class ActionBase(BaseModel):
    """Base class for all AI actions."""
    action_type: IntentType = Field(description="The type of action to execute")


class CreateTaskAction(ActionBase):
    """Parameters for creating a new task."""
    action_type: IntentType = IntentType.CREATE_TASK
    title: str = Field(description="Task title")
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    priority: str = Field(default="MEDIUM")
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    source: str = Field(default="ai_assistant")


class UpdateTaskAction(ActionBase):
    """Parameters for updating an existing task."""
    action_type: IntentType = IntentType.UPDATE_TASK
    task_id: uuid.UUID
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    estimated_minutes: Optional[int] = None


class CompleteTaskAction(ActionBase):
    """Parameters for completing a task."""
    action_type: IntentType = IntentType.COMPLETE_TASK
    task_id: uuid.UUID


class ChangeTaskStatusAction(ActionBase):
    """Parameters for changing task status."""
    action_type: IntentType = IntentType.CHANGE_TASK_STATUS
    task_id: uuid.UUID
    new_status: str = Field(description="New status: TODO, IN_PROGRESS, REVIEW, COMPLETED")


class ChangeTaskPriorityAction(ActionBase):
    """Parameters for changing task priority."""
    action_type: IntentType = IntentType.CHANGE_TASK_PRIORITY
    task_id: uuid.UUID
    new_priority: str = Field(description="New priority: LOW, MEDIUM, HIGH, URGENT")


class SearchTasksAction(ActionBase):
    """Parameters for searching tasks."""
    action_type: IntentType = IntentType.SEARCH_TASKS
    search_query: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    client_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    label: Optional[str] = None


class GetTodayTasksAction(ActionBase):
    """Parameters for getting today's tasks."""
    action_type: IntentType = IntentType.GET_TODAY_TASKS


class GetOverdueTasksAction(ActionBase):
    """Parameters for getting overdue tasks."""
    action_type: IntentType = IntentType.GET_OVERDUE_TASKS


class GetProjectInfoAction(ActionBase):
    """Parameters for getting project information."""
    action_type: IntentType = IntentType.GET_PROJECT_INFO
    project_id: Optional[uuid.UUID] = None
    project_name: Optional[str] = None


class GetClientInfoAction(ActionBase):
    """Parameters for getting client information."""
    action_type: IntentType = IntentType.GET_CLIENT_INFO
    client_id: Optional[uuid.UUID] = None
    client_name: Optional[str] = None


class GeneralQuestionAction(ActionBase):
    """Parameters for answering a general question."""
    action_type: IntentType = IntentType.GENERAL_QUESTION
    question: str = Field(description="The user's question")


# Type alias for any action
ActionType = (
    CreateTaskAction
    | UpdateTaskAction
    | CompleteTaskAction
    | ChangeTaskStatusAction
    | ChangeTaskPriorityAction
    | SearchTasksAction
    | GetTodayTasksAction
    | GetOverdueTasksAction
    | GetProjectInfoAction
    | GetClientInfoAction
    | GeneralQuestionAction
)
