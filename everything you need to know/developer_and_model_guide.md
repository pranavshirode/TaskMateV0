# TaskMate AI — Developer & Incoming Model Reference Guide

> **Notice for Incoming AI Models & Engineers**:
> Read this document first. This guide contains the authoritative architecture, database schema, tool registry, API contracts, and coding rules. You do **not** need to scan every individual file in the repository to understand how the system works or where to implement new features.

---

## 1. High-Level Architecture & Monorepo Map

TaskMate AI is structured as a TypeScript/Python monorepo:

```
TaskMateV0/
├── apps/
│   ├── api/                          # FastAPI Backend Application (Python 3.12)
│   │   ├── app/
│   │   │   ├── agent/                # Multi-Step Bounded Agent Engine (Sprint 3)
│   │   │   │   ├── orchestrator.py   # Bounded agent loop (ReAct step engine)
│   │   │   │   ├── permissions.py    # ToolPermissionService (Write approval checks)
│   │   │   │   ├── prompts.py        # System prompt for agent reasoning
│   │   │   │   └── tools/            # Validated Tool implementations
│   │   │   │       ├── base.py       # AgentTool base class, ToolResult, ToolContext
│   │   │   │       ├── registry.py   # ToolRegistry whitelist & default loader
│   │   │   │       ├── task_tools.py # Task management tools (CRUD, status, priority)
│   │   │   │       ├── project_tools.py # Project listing & inspection
│   │   │   │       ├── client_tools.py  # Client CRM lookup tools
│   │   │   │       ├── github_tools.py  # GitHub API tools (repos, issues, PRs)
│   │   │   │       └── requirements_tools.py # Requirements analysis inspection tools
│   │   │   ├── ai/                   # AI Foundation & Extractors (Sprint 2 & 4)
│   │   │   │   ├── context/          # ContextBuilder & EntityResolver (fuzzy matcher)
│   │   │   │   ├── extractors/       # RequirementsAnalyzer (dynamic brief parsing)
│   │   │   │   ├── prompts/          # Versioned prompt templates
│   │   │   │   ├── providers/        # AIProvider abstraction (OpenAI & Mock)
│   │   │   │   ├── schemas/          # IntentType, ExtractedEntities, Responses
│   │   │   │   └── services/         # AIOrchestrator (single-turn router)
│   │   │   ├── api/                  # API Gateway & Routers
│   │   │   │   ├── dependencies.py   # FastAPI dependency injection (get_current_user, services)
│   │   │   │   ├── router.py         # Root API router mounting /api/v1/*
│   │   │   │   └── routes/           # Route handlers (auth, tasks, projects, agent, etc.)
│   │   │   ├── core/                 # Core Infrastructure
│   │   │   │   ├── config.py         # Pydantic BaseSettings (.env loading)
│   │   │   │   ├── encryption.py     # Symmetric Fernet token encryption
│   │   │   │   ├── errors.py         # Custom application exceptions & error handlers
│   │   │   │   ├── logging.py        # Structured JSON logger
│   │   │   │   └── security.py       # Bcrypt password hashing & JWT handling
│   │   │   ├── db/                   # Database Connection
│   │   │   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   │   │   └── session.py        # AsyncEngine & async_sessionmaker
│   │   │   ├── integrations/         # External Third-Party Clients
│   │   │   │   └── github/           # Async httpx GitHub REST client & schemas
│   │   │   ├── models/               # SQLAlchemy 2.0 ORM Declarations (20+ entities)
│   │   │   ├── repositories/         # Data Access Layer (Strict Tenant Scoping)
│   │   │   ├── schemas/              # Pydantic v2 Request/Response Validation Schemas
│   │   │   └── services/             # Business Logic & Domain Services
│   │   ├── alembic/                  # Alembic Database Migrations (001 - 005)
│   │   └── tests/                    # 103 Automated Tests (Pytest)
│   └── web/                          # Next.js 14 Frontend Application (React 18 + Tailwind)
│       ├── app/                      # Next.js App Router (24 Pages)
│       │   ├── page.tsx              # Public Landing Page
│       │   ├── login/ & register/    # Authentication Views
│       │   ├── dashboard/ or /       # Today Overview Cockpit
│       │   ├── tasks/                # Kanban & Task Board View
│       │   ├── projects/             # Project Management Views
│       │   ├── clients/              # CRM Views
│       │   ├── assistant/            # Multi-Step AI Agent Assistant Chat
│       │   ├── requirements/         # Requirements Matrix & Decomposition View
│       │   └── settings/             # Integration Settings (GitHub OAuth)
│       ├── components/               # UI Components (Sidebar, Navbar, Modals, Badges)
│       └── lib/                      # api-client.ts, auth-context.tsx, utils
├── docs/                             # Architecture Specs & Technical Audit Report
├── everything you need to know/      # Complete Orientation, Research & Setup Manuals
├── scripts/                          # seed.py (Demo data), setup.sh
├── docker-compose.yml                # Docker Compose (Postgres, API, Web)
├── Makefile                          # Standardized developer CLI targets
└── .env.example                      # Reference environment variables
```

---

## 2. Complete Database Model Reference (Entity Dictionary)

All tables inherit from `Base` (`app.db.base`). Every model enforces strict tenant isolation via `user_id`.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 USERS                                       │
│ id (PK, UUID) | name | email (UNIQUE) | password_hash | is_active           │
└──────┬───────────────────────┬───────────────────────┬──────────────────────┘
       │ 1:N                   │ 1:N                   │ 1:N
       ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌─────────────────────────────┐
│   CLIENTS    │        │   PROJECTS   │        │     AGENT_EXECUTIONS        │
│ id, user_id  │        │ id, user_id  │        │ id, user_id, status         │
│ name, status │        │ client_id    │        │ current_step, total_tokens  │
└──────┬───────┘        └──────┬───────┘        └──────────────┬──────────────┘
       │                       │                               │ 1:N
       │                       ├────────────────┐              ▼
       │                       │ 1:N            │ 1:N   ┌─────────────────────┐
       │                       ▼                ▼       │AGENT_EXECUTION_STEPS│
       │                ┌──────────────┐ ┌────────────┐ │ id, execution_id    │
       │                │    TASKS     │ │REQUIREMENTS│ │ tool_name, status   │
       │                │ id, user_id  │ │_ANALYSES   │ └─────────────────────┘
       │                │ project_id   │ │ id, user_id│
       │                │ status, prio │ │ project_id │
       │                └──────┬───────┘ └──────┬─────┘
       │                       │ 1:N            │ 1:N
       │                       ▼                ▼
       │                ┌──────────────┐ ┌────────────┐
       │                │ TASK_EVENTS  │ │REQUIREMENTS│
       │                │ (Audit log)  │ │ (FR/NFR)   │
       │                └──────────────┘ └──────┬─────┘
       │                                        │
       └────────────────────────────────────────┴────────┐
                                                         ▼
                                              ┌─────────────────────┐
                                              │REQUIREMENT_TASK_LINK│
                                              │(Bidirectional Trace)│
                                              └─────────────────────┘
```

### Table Catalog:
1. **`users`**: Registered developers. Password hashed with Bcrypt.
2. **`clients`**: Freelance clients (`LEAD`, `ACTIVE`, `COMPLETED`, `ARCHIVED`).
3. **`projects`**: Development projects linked to clients (`PLANNING`, `ACTIVE`, `ON_HOLD`, `COMPLETED`, `ARCHIVED`).
4. **`repositories`**: Linked code repositories (GitHub, GitLab) with URL and default branch.
5. **`tasks`**: Granular engineering work units (`TODO`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `COMPLETED`).
6. **`task_labels`** & **`task_label_associations`**: M:N tagging taxonomy.
7. **`task_events`**: Immutable audit stream capturing who, when, and what changed on a task.
8. **`agent_executions`**: Tracks bounded agent sessions, objective, status (`RUNNING`, `WAITING_FOR_APPROVAL`, `COMPLETED`, `FAILED`, `TIMEOUT`), and token usage.
9. **`agent_execution_steps`**: Granular log of each tool call, inputs, latency, and sanitized outputs.
10. **`github_integrations`**: Stores GitHub OAuth/PAT tokens encrypted at rest via Fernet.
11. **`requirements_analyses`**: Requirements extraction session for a project brief.
12. **`requirements`**: Individual functional (`FR`) and non-functional (`NFR`) requirements.
13. **`clarification_questions`**: AI-generated questions (`Q-1`, `Q-2`) resolving ambiguities.
14. **`requirement_assumptions`**: Explicit assumptions (`A-1`) logged during brief analysis.
15. **`requirement_risks`**: Technical/timeline risks (`R-1`) with severity ratings.
16. **`analysis_revisions`**: Immutable JSON snapshot of analysis versions upon re-analysis.
17. **`requirement_task_links`**: Bidirectional traceability mapping requirements to generated tasks.
18. **`project_context_notes`**: Persistent architectural memory and decisions.
19. **`client_requests`**: Inbound client brief/change request with impact analysis.
20. **`automation_executions`**: Audit trail for background/scheduled automations.

---

## 3. The Complete Agent Tool Registry

Every tool extends `AgentTool` (`app.agent.tools.base.AgentTool`) and is registered in `ToolRegistry`. Unregistered tools cannot be executed by the LLM.

| Tool Name | Permission | Target Domain | Description & Input Arguments |
|---|---|---|---|
| `task.create` | `WRITE` | Task Management | Creates a task. Args: `title` (str, req), `project_id` (str), `priority` (LOW/MED/HIGH/URGENT), `due_date` (YYYY-MM-DD), `description` (str). |
| `task.get` | `READ` | Task Management | Retrieves a task by ID. Args: `task_id` (str, req). |
| `task.search` | `READ` | Task Management | Searches tasks. Args: `query` (str), `project_id` (str), `status` (str), `priority` (str). |
| `task.update` | `WRITE` | Task Management | Updates fields. Args: `task_id` (str, req), `title`, `description`, `due_date`. |
| `task.change_status` | `WRITE` | Task Management | Transitions task status. Args: `task_id` (str, req), `status` (TODO/IN_PROGRESS/REVIEW/COMPLETED). |
| `task.change_priority`| `WRITE` | Task Management | Changes priority. Args: `task_id` (str, req), `priority` (LOW/MEDIUM/HIGH/URGENT). |
| `project.get` | `READ` | Project Management | Gets project metadata. Args: `project_id` (str, req). |
| `project.list` | `READ` | Project Management | Lists active projects for user. Args: `status` (str, opt). |
| `client.get` | `READ` | CRM | Retrieves client details. Args: `client_id` (str, req). |
| `client.list` | `READ` | CRM | Lists clients. Args: `status` (str, opt). |
| `github.repository.get` | `READ` | GitHub Integration | Gets repo info. Args: `owner` (str, req), `repo` (str, req). |
| `github.repository.list` | `READ` | GitHub Integration | Lists authenticated user's repositories. Args: none. |
| `github.issue.get` | `READ` | GitHub Integration | Gets issue details. Args: `owner` (str), `repo` (str), `issue_number` (int). |
| `github.issue.list` | `READ` | GitHub Integration | Lists issues for repo. Args: `owner` (str), `repo` (str), `state` (open/closed). |
| `github.pull_request.get` | `READ` | GitHub Integration | Gets PR info. Args: `owner` (str), `repo` (str), `pr_number` (int). |
| `github.pull_request.list` | `READ` | GitHub Integration | Lists PRs for repo. Args: `owner` (str), `repo` (str), `state` (open/closed). |
| `requirements.get_analysis` | `READ` | Requirements | Retrieves requirements analysis with questions. Args: `analysis_id` (str, req). |
| `requirements.list_for_project`| `READ` | Requirements | Lists all analyses for a project. Args: `project_id` (str, req). |

### Write Action Safety Rule:
When `AGENT_REQUIRE_APPROVAL_FOR_WRITES=True` in config, any tool with `permission = ToolPermission.WRITE` causes the `ToolPermissionService` to set `requires_approval = True`. The `AgentOrchestrator` immediately halts execution, sets `execution.status = "WAITING_FOR_APPROVAL"`, and requests user confirmation in the UI.

---

## 4. Key API Endpoints & Routes

All routes are mounted under `/api/v1` in `app.api.router.py`:

```
POST   /api/v1/auth/register             # Register new developer account
POST   /api/v1/auth/login                # Authenticate and receive Bearer JWT
GET    /api/v1/auth/me                   # Get profile of current user

GET    /api/v1/dashboard/today           # High-speed overview of today's work
GET    /api/v1/tasks                     # List & filter tasks (pagination supported)
POST   /api/v1/tasks                     # Create new task
PATCH  /api/v1/tasks/{id}                # Update task fields
PATCH  /api/v1/tasks/{id}/status         # Update status (records task_event)
PATCH  /api/v1/tasks/{id}/priority       # Update priority (records task_event)

GET    /api/v1/projects                  # List user projects
POST   /api/v1/projects                  # Create project
GET    /api/v1/clients                   # List CRM clients
POST   /api/v1/clients                   # Create CRM client

POST   /api/v1/agent/run                 # Execute multi-step bounded agent workflow

POST   /api/v1/requirements             # Submit brief for dynamic AI extraction
GET    /api/v1/requirements/{id}         # Get structured requirements, questions, risks
POST   /api/v1/requirements/{id}/clarify # Submit answers to clarification questions
POST   /api/v1/requirements/{id}/approve # Approve requirements specification
POST   /api/v1/requirements/{id}/generate-tasks # Propose WBS task breakdown
POST   /api/v1/requirements/{id}/approve-tasks  # Batch create tasks with traceability links

GET    /api/v1/integrations/github/status # Check GitHub OAuth connection status
POST   /api/v1/integrations/github/connect# Save GitHub access token (Fernet encrypted)
```

---

## 5. Architectural Invariants for New Code

If you are an AI model or developer implementing new features, you **MUST** adhere to these immutable rules:

1. **The LLM Never Accesses the Database Directly**: The AI model only receives sanitized JSON/text context and emits JSON tool calls. All database queries and mutations must occur through domain services (`TaskService`, `ProjectService`, etc.).
2. **Tenant Scoping is Mandatory**: Never write a query without filtering by `user_id = current_user.id`. Even if an ID is a UUID, cross-user tampering must fail with `404 Not Found` or `403 Forbidden`.
3. **Pydantic Validation**: All request bodies must be validated with Pydantic v2 schemas (`app/schemas/*`). Never accept raw untyped dictionaries in route signatures.
4. **Tool Schema Completeness**: When adding a new tool to `app/agent/tools/`:
   - Define exact `input_schema` conforming to JSON Schema standards.
   - Designate permission level: `ToolPermission.READ` or `ToolPermission.WRITE`.
   - Register the tool in `create_default_registry()` (`app/agent/tools/registry.py`).
5. **No Breaking Migrations**: When modifying models, generate an Alembic revision (`make migration msg="describe_change"`). Never drop tables or destructive columns without backward-compatible defaults.

---

## 6. How to Run, Test, and Verify

### Running Backend Tests:
```bash
# In apps/api with active virtual environment:
pytest -v

# Run agent tests specifically:
pytest tests/test_agent/ -v

# Run requirements pipeline tests:
pytest tests/test_requirements/ -v
```

### Running Frontend Checks:
```bash
# In apps/web:
npm run build   # Verifies TypeScript compiler and App Router page generation
```

### Applying Migrations:
```bash
cd apps/api
alembic upgrade head
```

---

## 7. Missing Implementations (V1 Gap Reference)

The following components are **specified in the V1 scope** but **not yet implemented** in the codebase. Any AI model or engineer picking up this project should check this list before adding new features to avoid duplication, and should implement these before adding anything outside V1 scope.

> See `context.md` Section 7 for full details, completion percentages, and the prioritized action plan.

### 7.1 Missing Database Models

| Model Name | Table Name | Migration File | Purpose |
|---|---|---|---|
| `Proposal` | `proposals` | `006_proposals.py` | SOW document linked to project + requirements |
| `ProposalItem` | `proposal_items` | `006_proposals.py` | Line-item effort estimation per requirement |
| `ClientCommunication` | `client_communications` | `007_comms_milestones.py` | Outbound/inbound message drafts |
| `ClientFollowUp` | `client_follow_ups` | `007_comms_milestones.py` | Scheduled follow-up reminders |
| `Milestone` | `milestones` | `007_comms_milestones.py` | Task phase grouping within a project |
| `TaskDependency` | `task_dependencies` | `007_comms_milestones.py` | Inter-task BLOCKED_BY / DEPENDS_ON links |

### 7.2 Missing Services

| Service Class | File Path | Depends On |
|---|---|---|
| `ProposalService` | `apps/api/app/services/proposal.py` | `ProposalRepository`, `RequirementsService`, `AIProvider` |
| `ClientCommunicationService` | `apps/api/app/services/client_communication.py` | `ClientCommunicationRepository`, `AIProvider` |
| `MilestoneService` | `apps/api/app/services/milestone.py` | `MilestoneRepository`, `TaskService` |

### 7.3 Missing Agent / Orchestration Components

| Component | File Path | Purpose |
|---|---|---|
| `WorkflowCoordinator` | `apps/api/app/agent/coordinator.py` | Chains RequirementsAnalyzer → TaskGenerator → ProposalAgent |
| `MCPClientManager` | `apps/api/app/integrations/mcp/client.py` | MCP JSON-RPC tool discovery and invocation adapter |

### 7.4 Missing API Routes

| Method + Path | Handler Location | Status |
|---|---|---|
| `POST /api/v1/projects/{id}/proposals` | `app/api/routes/proposals.py` | Not created |
| `GET /api/v1/projects/{id}/proposals` | `app/api/routes/proposals.py` | Not created |
| `GET /api/v1/agent/executions/{id}` | `app/api/routes/agent.py` | Not created |
| `POST /api/v1/workflows/brief-to-plan` | `app/api/routes/workflows.py` | Not created |
| `GET /api/v1/projects/{id}/milestones` | `app/api/routes/projects.py` | Not created |
| `POST /api/v1/projects/{id}/milestones` | `app/api/routes/projects.py` | Not created |

### 7.5 Missing Frontend Pages

| Route | File Path | Purpose |
|---|---|---|
| `/projects/[id]/proposals` | `apps/web/app/projects/[id]/proposals/page.tsx` | Proposal review and SOW view |
| `/assistant/executions/[id]` | `apps/web/app/assistant/executions/[id]/page.tsx` | Agent execution trace inspector |
| `/clients/[id]/communications` | `apps/web/app/clients/[id]/communications/page.tsx` | Client message drafting + approval UI |

### 7.6 Highest Priority Next Step

**Implement the Agent Observability UI (Gap 4 — Phase A):**

The backend for agent tracing is fully built. To complete it:
1. Add `GET /api/v1/agent/executions/{id}` route in `app/api/routes/agent.py` returning `AgentExecution` + all `AgentExecutionStep` records.
2. Create frontend page `apps/web/app/assistant/executions/[id]/page.tsx` showing a step-by-step trace with tool names, inputs, status badges, and latency.
3. Add a polling hook (every 2s while status is `RUNNING`) for live updates.

No new migration, no new model, no new service — it's purely a backend route + frontend page.
