"""Intent definitions and schema for AI-parsed intents."""

from __future__ import annotations

import enum

from pydantic import BaseModel, Field


class IntentType(str, enum.Enum):
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


class ExtractedEntities(BaseModel):
    """Entities extracted from natural language by the LLM."""

    task_title: str | None = None
    task_description: str | None = None
    project_name: str | None = None
    client_name: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: str | None = None
    labels: list[str] = Field(default_factory=list)
    search_query: str | None = None
    task_reference: str | None = None  # e.g. "the login bug task"
    estimated_minutes: int | None = None


class ParsedIntent(BaseModel):
    """The structured output the LLM returns after understanding a user message."""

    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    reasoning: str | None = None  # Internal only, never exposed to user
