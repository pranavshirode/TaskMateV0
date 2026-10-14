"""AI-specific error types."""


class AIError(Exception):
    """Base error for AI operations."""

    pass


class AIProviderError(AIError):
    """Error communicating with the AI provider."""

    pass


class AITimeoutError(AIProviderError):
    """AI provider request timed out."""

    pass


class AIRateLimitError(AIProviderError):
    """AI provider rate limit exceeded."""

    pass


class AIAuthenticationError(AIProviderError):
    """AI provider authentication failed."""

    pass


class AIResponseError(AIError):
    """AI returned an invalid or unparseable response."""

    pass


class AISchemaValidationError(AIError):
    """AI response failed schema validation."""

    pass


class AIEntityResolutionError(AIError):
    """Failed to resolve an entity from AI output to a database record."""

    def __init__(self, entity_type: str, entity_value: str, candidates: list | None = None):
        self.entity_type = entity_type
        self.entity_value = entity_value
        self.candidates = candidates or []
        count = len(self.candidates)
        if count == 0:
            msg = f"No {entity_type} found matching '{entity_value}'"
        else:
            msg = f"Multiple {entity_type}s found matching '{entity_value}': {count} candidates"
        super().__init__(msg)


class AIUnavailableError(AIError):
    """AI service is not configured or unavailable."""

    pass
