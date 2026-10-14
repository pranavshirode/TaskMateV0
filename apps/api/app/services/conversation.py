"""Service layer for conversation management."""

from __future__ import annotations

import uuid

from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User
from app.repositories.conversation import ConversationRepository


class ConversationService:
    """Business logic for conversation management."""

    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    async def get_or_create_conversation(
        self, user: User, conversation_id: str | uuid.UUID | None = None
    ) -> Conversation:
        if conversation_id:
            conversation = await self.repository.get_conversation(str(conversation_id), str(user.id))
            if conversation:
                return conversation
        return await self.repository.create_conversation(user_id=str(user.id))

    async def get_conversation(
        self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID | User
    ) -> Conversation | None:
        uid = user_id.id if hasattr(user_id, "id") else str(user_id)
        return await self.repository.get_conversation(str(conversation_id), str(uid))

    async def list_conversations(self, user: User, skip: int = 0, limit: int = 20) -> tuple[list[Conversation], int]:
        items = await self.repository.list_conversations(str(user.id), skip, limit)
        total = await self.repository.count_conversations(str(user.id))
        return items, total

    async def add_user_message(self, conversation_id: str | uuid.UUID, content: str) -> ConversationMessage:
        return await self.repository.add_message(
            conversation_id=str(conversation_id),
            role="user",
            content=content,
        )

    async def add_assistant_message(
        self,
        conversation_id: str | uuid.UUID,
        content: str,
        intent: str | None = None,
    ) -> ConversationMessage:
        return await self.repository.add_message(
            conversation_id=str(conversation_id),
            role="assistant",
            content=content,
            intent=intent,
        )

    async def get_recent_messages(self, conversation_id: str | uuid.UUID, limit: int = 10) -> list[ConversationMessage]:
        return await self.repository.get_recent_messages(str(conversation_id), limit)

    async def update_title(self, conversation: Conversation, title: str) -> Conversation:
        return await self.repository.update_conversation_title(conversation, title)
