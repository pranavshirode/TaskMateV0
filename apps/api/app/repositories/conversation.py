"""Repository for conversation and AI log persistence."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationMessage
from app.models.ai_log import AIRequestLog


class ConversationRepository:
    """Data access for conversations, messages, and AI logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---- Conversations ----

    async def create_conversation(self, user_id: uuid.UUID, title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Get a conversation by ID, scoped to the user."""
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[Conversation]:
        """List conversations for a user, newest first."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_conversations(self, user_id: uuid.UUID) -> int:
        """Count conversations for a user."""
        stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_conversation_title(
        self, conversation: Conversation, title: str
    ) -> Conversation:
        """Update a conversation's title."""
        conversation.title = title
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    # ---- Messages ----

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
        )
        self.session.add(message)
        # Update conversation's updated_at
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_recent_messages(
        self, conversation_id: uuid.UUID, limit: int = 10
    ) -> List[ConversationMessage]:
        """Get recent messages from a conversation for context."""
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(desc(ConversationMessage.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages

    # ---- AI Request Logs ----

    async def create_ai_log(
        self,
        user_id: uuid.UUID,
        provider: str,
        model: str,
        intent: Optional[str] = None,
        conversation_id: Optional[uuid.UUID] = None,
        status: str = "success",
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: int = 0,
        error_type: Optional[str] = None,
    ) -> AIRequestLog:
        """Create an AI request log entry."""
        log = AIRequestLog(
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            intent=intent,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            error_type=error_type,
        )
        self.session.add(log)
        await self.session.commit()
        return log

    async def get_usage_stats(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get AI usage statistics for a user."""
        # Total stats
        total_stmt = select(
            func.count(AIRequestLog.id).label("total_requests"),
            func.coalesce(func.sum(AIRequestLog.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(AIRequestLog.output_tokens), 0).label("total_output_tokens"),
            func.coalesce(func.sum(AIRequestLog.total_tokens), 0).label("total_tokens"),
            func.avg(AIRequestLog.latency_ms).label("avg_latency_ms"),
        ).where(AIRequestLog.user_id == user_id)
        total_result = await self.session.execute(total_stmt)
        total_row = total_result.one()

        # Today's requests
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_stmt = select(func.count(AIRequestLog.id)).where(
            AIRequestLog.user_id == user_id,
            AIRequestLog.created_at >= today_start,
        )
        today_result = await self.session.execute(today_stmt)
        requests_today = today_result.scalar_one()

        # Error rate
        error_stmt = select(func.count(AIRequestLog.id)).where(
            AIRequestLog.user_id == user_id,
            AIRequestLog.status == "error",
        )
        error_result = await self.session.execute(error_stmt)
        error_count = error_result.scalar_one()
        total_requests = total_row.total_requests or 0
        error_rate = (error_count / total_requests) if total_requests > 0 else 0.0

        # Most common intent
        intent_stmt = (
            select(AIRequestLog.intent, func.count(AIRequestLog.id).label("cnt"))
            .where(
                AIRequestLog.user_id == user_id,
                AIRequestLog.intent.isnot(None),
            )
            .group_by(AIRequestLog.intent)
            .order_by(desc("cnt"))
            .limit(1)
        )
        intent_result = await self.session.execute(intent_stmt)
        intent_row = intent_result.first()
        most_common_intent = intent_row.intent if intent_row else None

        return {
            "total_requests": total_requests,
            "total_input_tokens": total_row.total_input_tokens,
            "total_output_tokens": total_row.total_output_tokens,
            "total_tokens": total_row.total_tokens,
            "requests_today": requests_today,
            "most_common_intent": most_common_intent,
            "average_latency_ms": round(float(total_row.avg_latency_ms), 1) if total_row.avg_latency_ms else None,
            "error_rate": round(error_rate, 4),
        }
