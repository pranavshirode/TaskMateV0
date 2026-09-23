# TaskMate AI — Developer Guide

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TaskMateAI
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start the development environment:
   ```bash
   make up
   ```

   This starts PostgreSQL, the FastAPI backend, and the Next.js frontend.

4. Run database migrations:
   ```bash
   make migrate
   ```

5. Verify the setup:
   - Backend health: http://localhost:8000/health
   - Backend readiness: http://localhost:8000/health/ready
   - System info: http://localhost:8000/api/v1/system/info
   - Frontend: http://localhost:3000

### Running Without Docker

If you prefer running services directly:

**Backend:**
```bash
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

**Database:**
Ensure PostgreSQL is running locally and update `DATABASE_URL` in `.env`.

## Developer Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services with Docker Compose |
| `make down` | Stop all services |
| `make build` | Build all Docker images |
| `make dev` | Start services in development mode |
| `make test` | Run all tests (backend + frontend) |
| `make lint` | Run all linters |
| `make format` | Auto-format all code |
| `make migrate` | Run database migrations |
| `make migration msg="description"` | Create a new migration |
| `make logs` | Tail service logs |
| `make clean` | Remove all containers and volumes |
| `make install` | Install all dependencies locally |

## Project Structure

```
TaskMateAI/
├── apps/
│   ├── api/           # FastAPI backend
│   │   ├── app/       # Application source code
│   │   ├── tests/     # Backend tests
│   │   └── alembic/   # Database migrations
│   └── web/           # Next.js frontend
│       ├── app/       # Pages and layouts
│       ├── components/# UI components
│       ├── lib/       # Utilities and API client
│       └── tests/     # Frontend tests
├── docs/              # Documentation
├── infrastructure/    # Docker and deployment configs
├── packages/          # Shared packages
├── scripts/           # Development scripts
└── .github/           # CI/CD workflows
```

## Adding New Features

### Backend

1. **Models**: Add SQLAlchemy models in `apps/api/app/models/`
2. **Schemas**: Add Pydantic schemas in `apps/api/app/schemas/`
3. **Repositories**: Add data access in `apps/api/app/repositories/`
4. **Services**: Add business logic in `apps/api/app/services/`
5. **Routes**: Add API endpoints in `apps/api/app/api/routes/`
6. **Register route**: Include new router in `apps/api/app/api/router.py`
7. **Migration**: Run `make migration msg="add_feature_table"`
8. **Tests**: Add tests in `apps/api/tests/`

### Frontend

1. **Components**: Add in `apps/web/components/`
2. **Pages**: Add in `apps/web/app/`
3. **API methods**: Add to `apps/web/lib/api-client.ts`
4. **Tests**: Add in `apps/web/tests/`

## Code Style

### Backend (Python)
- Formatter/Linter: Ruff
- Type checking: mypy
- Line length: 88 characters
- Import sorting: isort (via Ruff)

### Frontend (TypeScript)
- Linter: ESLint (Next.js config)
- Formatter: Prettier
- Strict TypeScript mode enabled

## Testing

### Backend
```bash
cd apps/api
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_health.py  # Run specific test file
```

### Frontend
```bash
cd apps/web
npm test                  # Run all tests
npm run test:watch        # Watch mode
```

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment name | `development` |
| `DATABASE_URL` | PostgreSQL connection string | (required) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `BACKEND_PORT` | Backend server port | `8000` |
