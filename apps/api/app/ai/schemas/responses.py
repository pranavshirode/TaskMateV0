"""Response schemas for AI operations.

These schemas define what the API returns to the frontend.
No internal reasoning, raw prompts, or chain-of-thought is exposed.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.ai.schemas.intent import IntentType


class AIActionResult(BaseModel):
    """Result of executing an AI-determined action."""
    action_type: IntentType
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class ContextSummary(BaseModel):
    """Summary of context used for the AI response.

    Displayed to the user to build trust. Does not
    expose raw data sent to the LLM.
    """
    task_count: int = 0
    project_count: int = 0
    overdue_count: int = 0
    due_today_count: int = 0


class AIChatRequest(BaseModel):
    """Request schema for the AI chat endpoint."""
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User's natural language message"
    )
    conversation_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional conversation ID for history continuity"
    )


class AIChatResponse(BaseModel):
    """Response from the AI chat endpoint.

    Contains only user-facing information. No internal
    reasoning, prompts, or chain-of-thought.
    """
    message: str = Field(description="AI's natural language response")
    intent: Optional[IntentType] = Field(None, description="Detected intent")
    confidence: Optional[float] = Field(None, description="Intent confidence")
    actions: list[AIActionResult] = Field(
        default_factory=list,
        description="Actions performed"
    )
    conversation_id: uuid.UUID = Field(description="Conversation ID")
    context_summary: Optional[ContextSummary] = Field(
        None,
        description="Summary of context used"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether the AI needs more information"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up actions or clarifications"
    )


class ConversationMessageResponse(BaseModel):
    """A single message in a conversation."""
    id: uuid.UUID
    role: str
    content: str
    intent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """A conversation with its messages."""
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse] = []

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """List of conversations."""
    items: list[ConversationResponse]
    total: int


class AIUsageResponse(BaseModel):
    """AI usage statistics for the current user."""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    requests_today: int = 0
    most_common_intent: Optional[str] = None
    average_latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
