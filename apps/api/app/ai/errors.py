"""AI-specific error types.

All errors map to user-safe messages. No API keys, prompts,
or internal reasoning are ever exposed.
"""

from app.core.errors import AppError


class AIError(AppError):
    """Base error for all AI operations."""
    def __init__(self, message: str, code: str = "AI_ERROR", status_code: int = 500):
        super().__init__(status_code=status_code, code=code, message=message)


class AIProviderError(AIError):
    """External AI provider returned an error."""
    def __init__(self, message: str = "AI service encountered an error. Your data is safe and unchanged."):
        super().__init__(message=message, code="AI_PROVIDER_ERROR", status_code=502)


class AITimeoutError(AIError):
    """AI provider request timed out."""
    def __init__(self, message: str = "AI request timed out. Please try again."):
        super().__init__(message=message, code="AI_TIMEOUT", status_code=504)


class AIRateLimitError(AIError):
    """AI provider rate limit exceeded."""
    def __init__(self, message: str = "AI rate limit exceeded. Please wait a moment and try again."):
        super().__init__(message=message, code="AI_RATE_LIMIT", status_code=429)


class AIAuthenticationError(AIError):
    """AI provider authentication failed."""
    def __init__(self, message: str = "AI service configuration error. Please contact support."):
        super().__init__(message=message, code="AI_AUTH_ERROR", status_code=500)


class AIResponseError(AIError):
    """AI returned an invalid or unparseable response."""
    def __init__(self, message: str = "AI produced an unexpected response. Please try rephrasing your request."):
        super().__init__(message=message, code="AI_RESPONSE_ERROR", status_code=500)


class AISchemaValidationError(AIError):
    """AI output failed schema validation."""
    def __init__(self, message: str = "AI response did not match expected format. Please try again."):
        super().__init__(message=message, code="AI_SCHEMA_ERROR", status_code=500)


class AIEntityResolutionError(AIError):
    """Entity could not be resolved unambiguously."""
    def __init__(self, message: str, code: str = "AI_ENTITY_ERROR"):
        super().__init__(message=message, code=code, status_code=400)


class AINotConfiguredError(AIError):
    """AI provider is not configured (missing API key etc)."""
    def __init__(self, message: str = "AI features are not configured. Please set AI_API_KEY."):
        super().__init__(message=message, code="AI_NOT_CONFIGURED", status_code=503)


class AIUserRateLimitError(AIError):
    """Per-user rate limit for AI endpoint exceeded."""
    def __init__(self, message: str = "You've reached the AI request limit. Please wait before trying again."):
        super().__init__(message=message, code="AI_USER_RATE_LIMIT", status_code=429)
