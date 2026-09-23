# TaskMate AI

> Agentic AI workspace for developer freelancers.

**Current target:** Developer Freelancers
**Current sprint:** Sprint 0 — Engineering Foundation

---

## What is TaskMate?

TaskMate AI is an intelligent workspace that helps developer freelancers manage their projects, tasks, client communications, and development workflows through AI-powered automation.

### Planned Capabilities

- Understand and convert client requests into actionable tasks
- Organize projects and prioritize daily work
- Interact with development tools (GitHub, etc.)
- Maintain project and client context
- Automate repetitive workflows
- Eventually use locally hosted AI models

## Architecture

```
┌──────────────────────────────────────────┐
│              Docker Compose              │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Next.js  │→│  FastAPI  │→│PostgreSQL│ │
│  │  :3000    │  │  :8000   │  │  :5432  │ │
│  └──────────┘  └──────────┘  └────────┘  │
└──────────────────────────────────────────┘
```

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Backend**: Python + FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker + Docker Compose

## Requirements

- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.10+
- [Docker](https://www.docker.com/) & Docker Compose
- [Git](https://git-scm.com/)

## Quick Start

### 1. Clone and configure

```bash
git clone <repository-url>
cd TaskMateAI
cp .env.example .env
```

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- PostgreSQL on port **5432**
- FastAPI backend on port **8000**
- Next.js frontend on port **3000**

### 3. Run database migrations

```bash
cd apps/api
alembic upgrade head
```

### 4. Verify

- **Frontend**: http://localhost:3000
- **Backend health**: http://localhost:8000/health
- **Backend readiness**: http://localhost:8000/health/ready
- **System info**: http://localhost:8000/api/v1/system/info

## Development Without Docker

### Backend

```bash
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

> **Note:** PostgreSQL must be running (via Docker or locally) and `DATABASE_URL` set in `.env`.

## Developer Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services with Docker Compose |
| `make down` | Stop all services |
| `make dev` | Start in foreground (attached) |
| `make test` | Run all tests |
| `make lint` | Run all linters |
| `make format` | Auto-format all code |
| `make migrate` | Run database migrations |
| `make migration msg="desc"` | Create new migration |
| `make install` | Install all dependencies locally |
| `make logs` | Tail service logs |
| `make clean` | Remove containers and volumes |

## Testing

### Backend
```bash
cd apps/api
pytest -v
```

### Frontend
```bash
cd apps/web
npm test
```

### All
```bash
make test
```

## Linting

### Backend
```bash
cd apps/api
ruff check .          # Lint
ruff format --check . # Check formatting
```

### Frontend
```bash
cd apps/web
npm run lint          # ESLint
npx prettier --check . # Check formatting
```

## Project Structure

```
TaskMateAI/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/         # API routes and router
│   │   │   ├── core/        # Config, logging, errors, middleware
│   │   │   ├── db/          # Database connection and base
│   │   │   ├── models/      # SQLAlchemy models
│   │   │   ├── schemas/     # Pydantic schemas
│   │   │   ├── services/    # Business logic
│   │   │   ├── repositories/# Data access layer
│   │   │   └── main.py      # Application factory
│   │   ├── tests/           # Backend tests
│   │   ├── alembic/         # Database migrations
│   │   └── pyproject.toml
│   │
│   └── web/                 # Next.js frontend
│       ├── app/             # Pages and layouts
│       ├── components/      # UI components
│       ├── lib/             # API client and utilities
│       └── tests/           # Frontend tests
│
├── docs/
│   ├── architecture/        # Architecture docs (current + future)
│   ├── development/         # Developer guide
│   └── api/                 # API reference
│
├── infrastructure/
│   └── docker/              # Dockerfiles
│
├── packages/
│   └── shared/              # Future shared contracts
│
├── scripts/                 # Setup and utility scripts
├── .github/workflows/       # CI pipeline
├── .env.example             # Environment template
├── docker-compose.yml       # Docker Compose config
├── Makefile                 # Developer commands
└── README.md                # This file
```

## Development Rules

- **Backend routes**: Add in `apps/api/app/api/routes/`, register in `router.py`
- **Backend models**: Add in `apps/api/app/models/`, create migration
- **Backend services**: Add business logic in `apps/api/app/services/`
- **Frontend pages**: Add in `apps/web/app/`
- **Frontend components**: Add in `apps/web/components/`
- **API methods**: Add to `apps/web/lib/api-client.ts`
- **Never commit**: `.env`, API keys, `node_modules`, `__pycache__`

## API Versioning

All business endpoints use the `/api/v1/` prefix. Health endpoints are unversioned.

## Documentation

- [Architecture Overview](docs/architecture/README.md)
- [AI Provider Architecture](docs/architecture/ai-provider.md) (future)
- [Agent Architecture](docs/architecture/agent.md) (future)
- [Developer Guide](docs/development/README.md)
- [API Reference](docs/api/README.md)

## License

Private — All rights reserved.
