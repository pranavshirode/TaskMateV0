# AI Provider Architecture

> ⚠️ **This document describes future architecture. AI provider integration is NOT part of Sprint 0.**

## Design Principle

TaskMate AI must NOT be tightly coupled to any single AI provider. The core application should function independently of the specific AI model or service being used.

## Provider Abstraction

```
AIProvider (Abstract Interface)
    │
    ├── ExternalProvider
    │   ├── OpenAIProvider
    │   ├── AnthropicProvider
    │   └── OtherCloudProvider
    │
    └── LocalModelProvider
        ├── OllamaProvider
        └── CustomModelProvider
```

## Interface Design

The `AIProvider` interface will define a common contract:

```python
# Conceptual interface — not yet implemented
class AIProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs) -> AIResponse:
        """Generate a completion from the AI model."""
        ...

    @abstractmethod
    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[AIChunk]:
        """Stream a completion from the AI model."""
        ...

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Return information about the current model."""
        ...
```

## Configuration

Provider selection will be driven by environment variables:

```env
AI_PROVIDER=openai        # or "anthropic", "ollama", "local"
AI_MODEL=gpt-4            # provider-specific model identifier
AI_API_KEY=sk-...         # API key (not needed for local models)
AI_BASE_URL=              # optional custom endpoint
```

## Development Strategy

```
V0/V1: External AI APIs (OpenAI, Anthropic)
    ↓
Stable agent architecture with provider abstraction
    ↓
Working developer freelancer product
    ↓
Local AI models (Ollama, custom)
    ↓
Fine-tuning / optimization
    ↓
Advanced versions V2–V5
```

## Key Requirements

1. **Provider switching**: Changing AI providers should require only configuration changes, not code changes in the core application.
2. **Graceful degradation**: The application should handle AI provider failures gracefully.
3. **Cost tracking**: The abstraction should support tracking token usage and costs.
4. **Rate limiting**: Built-in rate limiting per provider.
5. **Caching**: Response caching where appropriate to reduce costs.
6. **Testing**: Providers should be easily mockable for testing.

## Implementation Timeline

- **Sprint 0**: Architecture documentation (this document)
- **Sprint 1-2**: Base `AIProvider` interface and first external provider
- **Sprint 3+**: Local model support
- **Future**: Fine-tuning and optimization
