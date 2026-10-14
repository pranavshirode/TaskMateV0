"""AI API Routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.schemas.responses import (
    AIChatRequest,
    AIChatResponse,
    AIUsageResponse,
    ConversationDetailResponse,
    ConversationMessageResponse,
    ConversationResponse,
)
from app.ai.services.orchestrator import AIOrchestrator
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai import AIRequestLog, Conversation, ConversationMessage
from app.models.user import User

router = APIRouter()


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Interact with TaskMate AI using natural language."""
    orchestrator = AIOrchestrator(db=db)
    return await orchestrator.chat(
        user_id=current_user.id,
        message=payload.message,
        conversation_id=payload.conversation_id,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent AI conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(30)
    )
    conversations = list(result.scalars().all())

    summaries: list[ConversationResponse] = []
    for c in conversations:
        # Get message count and last message
        cnt_res = await db.execute(
            select(func.count(ConversationMessage.id)).where(ConversationMessage.conversation_id == c.id)
        )
        msg_count = cnt_res.scalar_one() or 0

        last_res = await db.execute(
            select(ConversationMessage.content)
            .where(ConversationMessage.conversation_id == c.id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(1)
        )
        last_msg = last_res.scalar_one_or_none()

        summaries.append(
            ConversationResponse(
                id=c.id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=msg_count,
                last_message=last_msg,
            )
        )

    return summaries


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full conversation history by conversation ID."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = [
        ConversationMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in conv.messages
    ]

    return ConversationDetailResponse(
        id=conv.id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conv)
    await db.commit()
    return None


@router.get("/usage", response_model=AIUsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI usage tokens and request stats for the user."""
    # Total stats
    tot_res = await db.execute(
        select(
            func.count(AIRequestLog.id),
            func.coalesce(func.sum(AIRequestLog.prompt_tokens), 0),
            func.coalesce(func.sum(AIRequestLog.completion_tokens), 0),
        ).where(AIRequestLog.user_id == current_user.id)
    )
    row = tot_res.one()
    total_reqs, prompt_tokens, comp_tokens = row[0], row[1], row[2]

    # Intent breakdown
    intents_res = await db.execute(
        select(ConversationMessage.intent, func.count(ConversationMessage.id))
        .join(Conversation, Conversation.id == ConversationMessage.conversation_id)
        .where(
            Conversation.user_id == current_user.id,
            ConversationMessage.role == "assistant",
            ConversationMessage.intent.isnot(None),
        )
        .group_by(ConversationMessage.intent)
    )
    by_intent = {r[0]: r[1] for r in intents_res.all() if r[0]}

    return AIUsageResponse(
        total_requests=total_reqs,
        total_input_tokens=prompt_tokens,
        total_output_tokens=comp_tokens,
        requests_today=total_reqs,
        tokens_today=prompt_tokens + comp_tokens,
        by_intent=by_intent,
    )
