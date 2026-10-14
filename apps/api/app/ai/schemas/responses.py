"""Response schemas for the AI chat API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AIActionResult(BaseModel):
    """Result of an AI-executed action."""

    type: str
    success: bool
    message: str
    data: dict | None = None  # e.g. created task data


class AIChatRequest(BaseModel):
    """Request body for POST /api/v1/ai/chat."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None


class AIChatResponse(BaseModel):
    """Response body from POST /api/v1/ai/chat."""

    message: str
    conversation_id: str
    intent: str | None = None
    confidence: float | None = None
    actions: list[AIActionResult] = Field(default_factory=list)
    context_summary: dict | None = None  # e.g. {"tasks": 3, "projects": 2}
    # True when the assistant is asking the user a question instead of acting.
    requires_clarification: bool = False


class ConversationResponse(BaseModel):
    """A conversation summary."""

    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None


class ConversationMessageResponse(BaseModel):
    """A single message in a conversation."""

    id: str
    role: str
    content: str
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    """A conversation with its messages."""

    id: str
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse] = Field(default_factory=list)


class AIUsageResponse(BaseModel):
    """AI usage statistics."""

    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    requests_today: int = 0
    tokens_today: int = 0
    by_intent: dict[str, int] = Field(default_factory=dict)
