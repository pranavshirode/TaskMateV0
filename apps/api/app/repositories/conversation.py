"""Repository for conversation and AI log persistence."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import AIRequestLog, Conversation, ConversationMessage


class ConversationRepository:
    """Data access for conversations, messages, and AI logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self, user_id: str | uuid.UUID, title: Optional[str] = None
    ) -> Conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            title=title or "New Conversation",
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID
    ) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == str(conversation_id),
                Conversation.user_id == str(user_id),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self, user_id: str | uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == str(user_id))
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_conversations(self, user_id: str | uuid.UUID) -> int:
        stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == str(user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def update_conversation_title(
        self, conversation: Conversation, title: str
    ) -> Conversation:
        conversation.title = title
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def add_message(
        self,
        conversation_id: str | uuid.UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=str(conversation_id),
            role=role,
            content=content,
            intent=intent,
        )
        self.session.add(message)
        stmt = select(Conversation).where(Conversation.id == str(conversation_id))
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_recent_messages(
        self, conversation_id: str | uuid.UUID, limit: int = 10
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == str(conversation_id))
            .order_by(desc(ConversationMessage.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

