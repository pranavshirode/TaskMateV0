# TaskMate AI

**Agentic AI workspace for developer freelancers.**

TaskMate AI helps developer freelancers manage clients, projects, tasks, and code repositories from a single workspace. The platform is designed to be AI-augmented (Sprint 2), but Sprint 1 delivers a fully functional developer workspace without any AI dependencies.

## Architecture

```
Frontend (Next.js)  →  Backend API (FastAPI)  →  PostgreSQL
```

### Backend Stack
- **FastAPI** — async web framework
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — production database
- **Alembic** — database migrations
- **JWT** — authentication (python-jose + passlib)
- **Pydantic v2** — request/response validation

### Frontend Stack
- **Next.js 14+** — React framework with App Router
- **TypeScript** — type safety
- **Tailwind CSS** — styling

### Key Design Principles
- Service → Repository → Database architecture
- Every query scoped by `user_id` for data isolation
- Same API serves both human UI and future AI agent
- Soft deletion (archival) over destructive deletes

## Quick Start

### One command (local, no Docker)

```bash
./hitme.sh        # or: make hitme
```

Installs what's missing, migrates the database, seeds the demo user (`alex@taskmate.dev` / `password123`), and starts the API and web app. It picks free ports automatically, and `Ctrl+C` stops both. See [DEMO.md](./DEMO.md) for the demo guide.

### Docker

```bash
# Start all services
docker compose up --build

# Run migrations
docker compose exec api alembic upgrade head

# Seed demo data
docker compose exec api python scripts/seed_db.py
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd apps/api
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

### Run Tests

```bash
cd apps/api
pip install -e ".[dev]"
pytest -v
```

## Demo Credentials

After running the seed script:
- **Email:** alex@taskmate.dev
- **Password:** password123

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| GET | `/api/v1/auth/me` | Current user profile |
| PATCH | `/api/v1/auth/me` | Update profile |
| GET/POST | `/api/v1/clients` | List/Create clients |
| GET/PATCH/DELETE | `/api/v1/clients/{id}` | Get/Update/Archive client |
| GET/POST | `/api/v1/projects` | List/Create projects |
| GET/PATCH/DELETE | `/api/v1/projects/{id}` | Get/Update/Archive project |
| GET/POST | `/api/v1/projects/{id}/repositories` | List/Add repos |
| GET/PATCH/DELETE | `/api/v1/repositories/{id}` | Get/Update/Delete repo |
| GET/POST | `/api/v1/tasks` | List/Create tasks |
| GET/PATCH/DELETE | `/api/v1/tasks/{id}` | Get/Update/Archive task |
| PATCH | `/api/v1/tasks/{id}/status` | Change status |
| PATCH | `/api/v1/tasks/{id}/priority` | Change priority |
| GET | `/api/v1/tasks/{id}/events` | Task activity log |
| GET | `/api/v1/dashboard/today` | Dashboard data |
| GET/POST | `/api/v1/labels` | List/Create labels |

## Project Structure

```
TaskMateAI/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/            # Routes & dependencies
│   │   │   ├── core/           # Config, security, errors
│   │   │   ├── db/             # Database setup
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── repositories/   # Data access layer
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Business logic
│   │   ├── alembic/            # Migrations
│   │   └── tests/              # Backend tests
│   └── web/                    # Next.js frontend
│       ├── app/                # Pages (App Router)
│       ├── components/         # React components
│       └── lib/                # API client, auth context
├── docs/                       # Documentation
├── scripts/                    # Seed data, utilities
└── docker-compose.yml
```

## Sprint 1 Scope

✅ User authentication (register/login/JWT)
✅ Client management (CRUD + archive + search)
✅ Project management (CRUD + archive + filter)
✅ Repository registration (manual, no GitHub API)
✅ Task management (full CRUD + status/priority + labels + events)
✅ Dashboard / Today view
✅ Frontend with all pages
✅ Data isolation per user
✅ API tests & E2E test workflows

## What's Next (Sprint 2)

Sprint 2 will introduce an AI agent layer that operates through the same API:
- LLM integration
- Agent tools wrapping the existing API
- Intelligent task suggestions
- Automated workflow assistance
