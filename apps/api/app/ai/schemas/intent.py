"""Intent definitions and schemas for AI understanding.

Intents represent the user's desired action as classified by the AI.
Each intent maps to a specific business operation.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported AI intents.

    Each intent maps to a specific business operation
    in the TaskMate workspace.
    """
    GENERAL_QUESTION = "GENERAL_QUESTION"
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    COMPLETE_TASK = "COMPLETE_TASK"
    CHANGE_TASK_STATUS = "CHANGE_TASK_STATUS"
    CHANGE_TASK_PRIORITY = "CHANGE_TASK_PRIORITY"
    SEARCH_TASKS = "SEARCH_TASKS"
    GET_TODAY_TASKS = "GET_TODAY_TASKS"
    GET_OVERDUE_TASKS = "GET_OVERDUE_TASKS"
    GET_PROJECT_INFO = "GET_PROJECT_INFO"
    GET_CLIENT_INFO = "GET_CLIENT_INFO"
    RUN_AGENT = "RUN_AGENT"


# Intents that mutate data
MUTATING_INTENTS = {
    IntentType.CREATE_TASK,
    IntentType.UPDATE_TASK,
    IntentType.COMPLETE_TASK,
    IntentType.CHANGE_TASK_STATUS,
    IntentType.CHANGE_TASK_PRIORITY,
    IntentType.RUN_AGENT,
}

# Intents that only read data
READ_ONLY_INTENTS = {
    IntentType.GENERAL_QUESTION,
    IntentType.SEARCH_TASKS,
    IntentType.GET_TODAY_TASKS,
    IntentType.GET_OVERDUE_TASKS,
    IntentType.GET_PROJECT_INFO,
    IntentType.GET_CLIENT_INFO,
}


class IntentResult(BaseModel):
    """Result of AI intent classification.

    This is the structured output expected from the LLM
    when classifying user intent.
    """
    intent: IntentType = Field(description="The classified intent type")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from the user message"
    )
    reasoning: str = Field(
        default="",
        description="Brief internal reasoning (not exposed to user)"
    )


class ExtractedEntities(BaseModel):
    """Common entities extracted from natural language.

    All fields are optional — the AI extracts what it can.
    """
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    project_name: Optional[str] = Field(None, description="Project name (to be resolved)")
    client_name: Optional[str] = Field(None, description="Client name (to be resolved)")
    task_name: Optional[str] = Field(None, description="Task name for lookup (to be resolved)")
    priority: Optional[str] = Field(None, description="Priority: LOW, MEDIUM, HIGH, URGENT")
    status: Optional[str] = Field(None, description="Status: TODO, IN_PROGRESS, REVIEW, COMPLETED")
    due_date: Optional[str] = Field(None, description="Due date expression (e.g., 'tomorrow', 'Friday', '2026-10-10')")
    label: Optional[str] = Field(None, description="Task label for filtering")
    search_query: Optional[str] = Field(None, description="Search terms for task lookup")
    estimated_minutes: Optional[int] = Field(None, description="Estimated time in minutes")
