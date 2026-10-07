"""AI Assistant API endpoints.

Provides natural language interaction with the TaskMate workspace.
"""

import logging
import time
import uuid
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.errors import AIError, AINotConfiguredError, AIUserRateLimitError
from app.ai.schemas.responses import (
    AIChatRequest,
    AIChatResponse,
    AIUsageResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationMessageResponse,
)
from app.api.dependencies import get_current_user, get_ai_orchestrator, get_conversation_service
from app.models.user import User
from app.services.conversation import ConversationService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple in-memory rate limiter (per-user, per-minute)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(user_id: str, max_per_minute: int) -> None:
    """Check per-user rate limit. Raises AIUserRateLimitError if exceeded."""
    now = time.time()
    window = 60.0  # 1 minute

    # Clean old entries
    _rate_limit_store[user_id] = [
        ts for ts in _rate_limit_store[user_id] if now - ts < window
    ]

    if len(_rate_limit_store[user_id]) >= max_per_minute:
        raise AIUserRateLimitError()

    _rate_limit_store[user_id].append(now)


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    request: AIChatRequest,
    user: User = Depends(get_current_user),
    orchestrator = Depends(get_ai_orchestrator),
):
    """Send a message to the AI assistant.

    The AI will understand the intent, extract entities,
    and execute the appropriate action through TaskMate services.
    """
    settings = get_settings()
    _check_rate_limit(str(user.id), settings.AI_RATE_LIMIT_PER_MINUTE)

    return await orchestrator.chat(
        user=user,
        message=request.message,
        conversation_id=request.conversation_id,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """List the user's AI conversations."""
    items, total = await conversation_service.list_conversations(user, skip, limit)
    return ConversationListResponse(
        items=[
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                messages=[],
            )
            for c in items
        ],
        total=total,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get a specific conversation with its messages."""
    conversation = await conversation_service.get_conversation(conversation_id, user)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ConversationMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                intent=m.intent,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )


@router.get("/usage", response_model=AIUsageResponse)
async def get_usage(
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get AI usage statistics for the current user."""
    stats = await conversation_service.get_usage_stats(user)
    return AIUsageResponse(**stats)
