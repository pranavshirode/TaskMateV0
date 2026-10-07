"""Service layer for conversation management."""

import uuid
from typing import Optional, Tuple, List, Dict, Any

from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User
from app.repositories.conversation import ConversationRepository


class ConversationService:
    """Business logic for conversation management."""

    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    async def get_or_create_conversation(
        self, user: User, conversation_id: Optional[uuid.UUID] = None
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            conversation = await self.repository.get_conversation(
                conversation_id, user.id
            )
            if conversation:
                return conversation
        # Create new conversation
        return await self.repository.create_conversation(user_id=user.id)

    async def get_conversation(
        self, conversation_id: uuid.UUID, user: User
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return await self.repository.get_conversation(conversation_id, user.id)

    async def list_conversations(
        self, user: User, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Conversation], int]:
        """List user's conversations."""
        items = await self.repository.list_conversations(user.id, skip, limit)
        total = await self.repository.count_conversations(user.id)
        return items, total

    async def add_user_message(
        self, conversation_id: uuid.UUID, content: str
    ) -> ConversationMessage:
        """Add a user message to a conversation."""
        return await self.repository.add_message(
            conversation_id=conversation_id,
            role="USER",
            content=content,
        )

    async def add_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        intent: Optional[str] = None,
    ) -> ConversationMessage:
        """Add an assistant message to a conversation."""
        return await self.repository.add_message(
            conversation_id=conversation_id,
            role="ASSISTANT",
            content=content,
            intent=intent,
        )

    async def get_recent_messages(
        self, conversation_id: uuid.UUID, limit: int = 10
    ) -> List[ConversationMessage]:
        """Get recent messages for conversation context."""
        return await self.repository.get_recent_messages(conversation_id, limit)

    async def update_title(
        self, conversation: Conversation, title: str
    ) -> Conversation:
        """Update conversation title."""
        return await self.repository.update_conversation_title(conversation, title)

    async def get_usage_stats(self, user: User) -> Dict[str, Any]:
        """Get AI usage statistics for the user."""
        return await self.repository.get_usage_stats(user.id)

    async def log_ai_request(
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
    ) -> None:
        """Log an AI request for observability."""
        await self.repository.create_ai_log(
            user_id=user_id,
            provider=provider,
            model=model,
            intent=intent,
            conversation_id=conversation_id,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            error_type=error_type,
        )
