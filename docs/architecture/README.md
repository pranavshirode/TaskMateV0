# TaskMate AI — Architecture Overview

## Current Architecture (Sprint 0)

TaskMate AI uses a standard three-tier architecture:

```
Browser (Next.js) → FastAPI Backend → PostgreSQL Database
```

### Frontend Layer

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Architecture**: Component-based with centralized API client
- **Port**: 3000 (development)

The frontend follows a clean component architecture:
- `app/` — Next.js App Router pages and layouts
- `components/` — Reusable UI components
- `lib/` — Utilities and API client

### Backend Layer

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Port**: 8000 (development)

The backend follows a layered architecture:
```
API Routes (app/api/routes/)
    ↓
Schemas (app/schemas/) — Request/Response validation
    ↓
Services (app/services/) — Business logic
    ↓
Repositories (app/repositories/) — Data access
    ↓
Models (app/models/) — Database models
    ↓
Database (app/db/) — Connection management
```

Cross-cutting concerns:
- `app/core/config.py` — Centralized configuration via Pydantic Settings
- `app/core/logging.py` — Structured JSON logging
- `app/core/errors.py` — Centralized error handling
- `app/core/middleware.py` — Request ID middleware

### Database Layer

- **Database**: PostgreSQL 16
- **Driver**: asyncpg (async)
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic with async support
- **Connection Pooling**: SQLAlchemy built-in (pool_size=5, max_overflow=10)

### API Design

- **Versioning**: `/api/v1/` prefix for all business endpoints
- **Health endpoints**: Unversioned (`/health`, `/health/ready`) — operational endpoints should not change with API versions
- **Error format**: Consistent JSON error responses with error code, message, and request ID
- **Request correlation**: UUID-based request IDs via `X-Request-ID` header

### Configuration

```
Environment Variables (.env)
    ↓
Pydantic Settings (app/core/config.py)
    ↓
Application Components
```

All configuration is centralized. Components never access `os.environ` directly.

### Logging

- Structured JSON format
- Fields: timestamp, level, service, request_id, event, message
- Configurable via `LOG_LEVEL` environment variable
- Sensitive data (passwords, API keys, tokens) is never logged

### Infrastructure

- **Docker Compose**: Three services (web, api, postgres)
- **Persistent storage**: PostgreSQL data via Docker volume
- **Health checks**: Docker health checks for all services
- **Networking**: Services communicate via Docker service names

---

## Future Architecture (Sprint 1+)

> ⚠️ **The following sections describe planned future architecture. None of these components are implemented yet.**

### Agent Layer

See [Agent Architecture](./agent.md) for details.

The agent layer will handle:
- Understanding client requests
- Task decomposition and planning
- Tool selection and execution
- Context management
- Response generation

### AI Provider Layer

See [AI Provider Architecture](./ai-provider.md) for details.

The AI provider layer will:
- Abstract AI model access behind a common interface
- Support multiple providers (OpenAI, local models, etc.)
- Enable provider switching without core application changes
- Eventually support locally hosted and fine-tuned models

### Tool Layer

Future tools for the agent:
- GitHub integration (repos, issues, PRs, code search)
- Communication tools (email, messaging)
- Calendar management
- Code analysis and generation
- Project/task management

### Memory Layer

Future memory systems:
- Conversation history
- Project context
- Client preferences
- Decision history
- Vector-based semantic search (RAG)

### Integration Layer

Future external integrations:
- GitHub API
- Gmail API
- Google Calendar API
- Notification services
- Payment processing
