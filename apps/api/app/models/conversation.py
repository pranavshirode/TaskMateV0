"""Re-export Conversation and ConversationMessage from app.models.ai for compatibility."""

from app.models.ai import Conversation, ConversationMessage

__all__ = ["Conversation", "ConversationMessage"]
