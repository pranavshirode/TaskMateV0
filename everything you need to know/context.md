# TaskMate AI — Project Context, Current State & Strategic Roadmap

---

## 1. Executive Context & Vision

### 1.1 Project Identity & Philosophy
**TaskMate AI** is an intelligent, multi-agent operations assistant and centralized workspace engineered specifically for **independent freelance software developers**. 

Freelancers operating as solo software developers shoulder two distinct workloads simultaneously:
1. **Engineering & Coding**: Architecture, backend/frontend engineering, database design, testing, CI/CD, debugging, and infrastructure.
2. **Operational & Administrative Overhead**: Client relationship management (CRM), requirements extraction from chaotic briefs/emails/chats, clarification Q&A, project scoping, task breakdown and milestone scheduling, proposal and estimation drafting, progress tracking, client update messages, and cross-system synchronization (e.g., GitHub, issue trackers).

Traditional project management suites (Jira, Linear, Asana, Monday) are designed for engineering teams or enterprise organizations; they demand high manual upkeep without automating the operational thinking. Conversely, generic AI chatbots (ChatGPT, Claude, Gemini) produce disconnected advice in a transient chat box without direct integration into a developer's real, persistent database.

**TaskMate AI eliminates this divide through one foundational principle:**
> **"AI that executes, not just advises."**
> The platform merges a unified developer workspace (CRM + Projects + Tasks + GitHub) with specialized, bounded AI agents capable of reasoning over requirements, invoking real backend services, mutating workspace state under human approval, maintaining bidirectional traceability, and persisting project memory across sessions.

---

## 2. The Final V1 Goal (Target State)

As detailed in the **Complete V1 Project Context Specification**, the ultimate objective of TaskMate AI V1 is to deliver a functional, robust operations assistant that automates the entire lifecycle of a freelance project:

```
[ Unstructured Client Brief / Chat ]
                 │
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                TaskMate AI Agent Platform                   │
 │                                                             │
 │  1. Unstructured Requirement Analysis                       │
 │     • Extract Functional & Non-Functional Requirements      │
 │     • Formulate Clarification Questions for Ambiguities     │
 │     • Identify Technical Risks, Assumptions & Scope Creep   │
 │                                                             │
 │  2. Developer Approval & Interactive Refinement             │
 │     • Human reviews, edits, and approves requirements       │
 │                                                             │
 │  3. Automated Task & Milestone Decomposition                │
 │     • Convert approved scope into actionable dev tasks      │
 │     • Bidirectional Traceability (Requirement ↔ Task)       │
 │     • Duplicate prevention and idempotency protection       │
 │                                                             │
 │  4. Developer Agent Execution with Tool Calling             │
 │     • Query/mutate internal CRM, Projects, Tasks            │
 │     • GitHub API Integration (issues, PRs, repos)           │
 │     • Bounded execution loop with write-approval gates      │
 │                                                             │
 │  5. Persistent Project Memory & Context Notes               │
 │     • Store architectural decisions and constraints         │
 │     • Context-aware multi-session AI continuity             │
 │                                                             │
 │  6. Daily Workflow Automations & Proactive Monitoring       │
 │     • Compute overdue tasks, deadlines, and daily agenda    │
 │     • Cross-system summaries and synchronization            │
 └─────────────────────────────────────────────────────────────┘
                 │
                 ▼
[ Verified, Persistent Production Database (PostgreSQL / SQLite) ]
```

### Core V1 Guarantees:
- **No Fabrications (Zero Silent Assumptions)**: If information is missing (e.g., missing deadline, ambiguous client reference), the AI formulates a targeted clarification question rather than hallucinating facts.
- **Tenant Isolation**: Every database query and tool call is strictly scoped to `user_id = current_user.id`.
- **Deterministic Separation**: Business rules, permissions, token encryption, and database writes are handled by deterministic backend code, never entrusted to the LLM.
- **Human-in-the-Loop (HITL)**: All mutating operations (write actions, requirement task creation, status updates) require human review or approval.
- **Auditability & Observability**: Every agent execution, tool call step, task status change, and requirement revision is logged with timestamps and execution metadata.

---

## 3. How Much is Done? (Detailed Sprint-by-Sprint Audit)

The repository has progressed through five comprehensive engineering phases (Sprint 0 through Sprint 4). All core backend pipelines and frontend cockpits have been implemented, tested, and audited.

### 3.1 Sprint 0 — Engineering Foundation
- **Monorepo Architecture**: Clean separation between `apps/api` (FastAPI + SQLAlchemy 2.0 Asyncio) and `apps/web` (Next.js 14 App Router + TailwindCSS).
- **Containerization & CI**: Multi-service `docker-compose.yml` (PostgreSQL 16, FastAPI backend, Next.js frontend). GitHub Actions workflow (`.github/workflows/ci.yml`) covering linting, type checks, backend tests, and frontend build.
- **Database Engine & Migrations**: Async engine (`asyncpg` for PostgreSQL, `aiosqlite` for local dev/testing) with Alembic migration pipeline.
- **Observability**: Centralized JSON structured logging, custom error classes (`AppError`, `NotFoundError`, `ForbiddenError`, `ValidationError`), request ID correlation middleware, and health endpoints (`/health`, `/health/ready`).

### 3.2 Sprint 1 — Core Developer Workspace
- **Authentication & Security**: User registration, login, and profile management using Argon2/Bcrypt password hashing and stateless HMAC-SHA256 JWT tokens.
- **Client CRM**: Full CRUD for freelance clients (names, contact info, notes, relationship statuses: `LEAD`, `ACTIVE`, `COMPLETED`, `ARCHIVED`).
- **Project Management**: Multi-project management linked to clients, tracking start dates, deadlines, and statuses (`PLANNING`, `ACTIVE`, `ON_HOLD`, `COMPLETED`, `ARCHIVED`).
- **Task Management**: Comprehensive task tracking with priorities (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), statuses (`BACKLOG`, `TODO`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `COMPLETED`), custom labels, due dates, and time estimates.
- **Task Audit Log**: `task_events` recording every status, priority, or deadline change with previous and new values.
- **Today Dashboard**: High-speed `/api/v1/dashboard/today` endpoint computing active projects, tasks due today, and overdue items.

### 3.3 Sprint 2 — AI Foundation & Intelligent Understanding
- **AI Provider Abstraction**: Provider-agnostic `AIProvider` base class supporting OpenAI (`gpt-4o`, `gpt-4o-mini`) and deterministic `MockAIProvider` for test reproducibility.
- **Context Builder**: Dynamic assembly of user-specific workspace context (active projects, pending tasks, client rosters) injected into prompt templates.
- **Entity Resolution & Fuzzy Matching**: Trigram/Levenshtein matching to resolve fuzzy entity names ("auth bug", "Rahul's redesign") to exact UUIDs in the database.
- **Intent Engine**: Classification across core intents (`CREATE_TASK`, `UPDATE_TASK`, `SEARCH_TASKS`, `GET_TODAY_TASKS`, `GET_OVERDUE_TASKS`, `GET_PROJECT_INFO`, `GET_CLIENT_INFO`).
- **Defensive Prompt Engineering**: Hardened system prompts preventing prompt injection and enforcing structured JSON responses.

### 3.4 Sprint 3 — Developer Agent, Tool Calling & GitHub Integration
- **Bounded Agent Orchestrator**: Multi-step ReAct-style agent loop (`AgentOrchestrator`) executing bounded iterations (`AGENT_MAX_STEPS = 10`, `AGENT_MAX_TOOL_CALLS = 10`, `AGENT_MAX_EXECUTION_TIME = 120s`).
- **Tool Registry**: Explicit registration of validated tools with strict JSON schemas. Unregistered tools cannot be called.
- **Internal Domain Tools**:
  - Task tools: `task.create`, `task.get`, `task.search`, `task.update`, `task.change_status`, `task.change_priority`.
  - Project tools: `project.get`, `project.list`.
  - Client tools: `client.get`, `client.list`.
- **GitHub Integration**:
  - Custom async HTTP client (`httpx`) communicating with GitHub REST API v3.
  - Read-only GitHub tools: `github.repository.get`, `github.repository.list`, `github.issue.get`, `github.issue.list`, `github.pull_request.get`, `github.pull_request.list`.
  - Secure credential storage: GitHub access tokens are encrypted at rest using symmetric Fernet encryption (`app/core/encryption.py`).
- **Permission & Approval Service**: `ToolPermissionService` evaluating each tool call. Mutating/write operations trigger `WAITING_FOR_APPROVAL` when `AGENT_REQUIRE_APPROVAL_FOR_WRITES = True`.
- **Agent Tracing & Observability**: Complete persistence of agent executions (`agent_executions`) and individual tool invocation steps (`agent_execution_steps`) with latency and outcome logging.

### 3.5 Sprint 4 — Requirements Analysis, Project Memory & Workflow Automations
- **Dynamic Requirements Extraction**: Specialized pipeline (`app/services/requirements_pipeline.py` & `app/ai/extractors/requirements_analyzer.py`) extracting:
  - Functional Requirements (`FR-x`) and Non-Functional Requirements (`NFR-x`).
  - Clarification Questions (`Q-x`) with underlying reasoning for ambiguities.
  - Explicit Assumptions (`A-x`) and Implementation Risks (`R-x`) with severity ratings.
  - Technical architecture constraints and scope boundaries.
- **Clarification Q&A Loop**: Endpoint and UI to answer clarifying questions, triggering versioned re-analysis (`AnalysisRevision`) without losing existing progress.
- **Automated Task Planning with Duplicate Protection**:
  - Generates recommended development tasks from approved requirements.
  - Idempotent creation: detects existing tasks to prevent duplicate records upon rerun.
  - Bidirectional Traceability: `requirement_task_links` table mapping every requirement to generated tasks (`IMPLEMENTS`, `TESTS`, `DOCUMENTS`).
- **Project Memory (Context Notes)**:
  - `project_context_notes` storing architectural decisions, framework choices, and constraints.
  - Automatic injection of confirmed context notes into subsequent AI sessions.
- **Workflow Automations**:
  - Daily summary generator analyzing stored task events, completed items, and overdue work.
  - Audit trail in `automation_executions`.
- **Frontend Cockpit**:
  - Dedicated pages for `/requirements`, `/projects/[id]/requirements/[analysisId]`, `/projects/[id]/context`, and `/projects/[id]/requests`.

### 3.6 Verification & Audit Metrics Summary
| Metric Category | Verified State | Details |
|---|---|---|
| **Backend Test Suite** | **103 / 103 Passing (100%)** | Unit, integration, E2E, and AI evaluation tests in `apps/api/tests/` |
| **Frontend Production Build** | **Success (0 Errors)** | `npm run build` compiles all 24 Next.js App Router pages cleanly |
| **Database Migrations** | **5 Migrations Applied** | Alembic versions `001` through `005` verified on SQLite and PostgreSQL |
| **Database Seed** | **Verified Working** | `python scripts/seed.py` creates complete demo workspace (`alex@taskmate.dev`) |
| **Security Audit** | **Passed** | Tenant data isolation, Fernet token encryption, Bcrypt passwords, secret masking |

---

## 4. Current Architecture Overview

```
                                [ Developer / Browser ]
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │      Next.js 14 Frontend Cockpit        │
                      │  (App Router, React 18, TailwindCSS)    │
                      └────────────────────┬────────────────────┘
                                           │ HTTP / JSON (Bearer JWT)
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │           FastAPI Gateway               │
                      │   (CORS, RequestID, Error Handling)     │
                      └────────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  Business Layer  │             │ AI Orchestrator  │             │   Agent Engine   │
│  - TaskService   │             │  - ContextBuilder│             │  - Tool Registry │
│  - ProjectService│             │  - Intent Engine │             │  - GitHub Tools  │
│  - Requirements  │             │  - AIProvider    │             │  - Bounded Loop  │
│  - ContextService│             │    (OpenAI/Mock) │             │  - Permissions   │
└────────┬─────────┘             └─────────┬────────┘             └─────────┬────────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │      Database Layer (SQLAlchemy 2.0)    │
                      │       PostgreSQL 16 / SQLite + Async    │
                      └─────────────────────────────────────────┘
```

---

## 5. What is the Next Step? (Remaining Scope for Production / V2)

While the core V1 developer-freelancer loop is complete and verified, the following enhancements constitute the immediate next steps to evolve TaskMate AI into a commercial-grade, multi-agent SaaS platform:

### Step 1: Frontend Jest & ESLint Modernization
- **Issue**: Frontend production build (`npm run build`) succeeds, but legacy unit tests in `apps/web/tests/` (written in Sprint 0) experience mock drift with Sprint 4 AuthContext.
- **Action**: Update Jest mocks with `<AuthProvider>` wrappers and resolve `@typescript-eslint/no-explicit-any` annotations across `api-client.ts`.

### Step 2: Background Task Worker (Celery / ARQ / Redis)
- **Current State**: Daily summaries and GitHub status synchronizations execute synchronously within HTTP request cycles.
- **Action**: Introduce an asynchronous background worker (e.g., Redis + ARQ or Celery) to run scheduled cron jobs, continuous repo event polling, and long-running document analyses out of band.

### Step 3: Multi-Agent Specialized Pipeline Coordination
- **Current State**: The Requirements Analyst and Agent Orchestrator operate as robust standalone pipelines.
- **Action**: Formalize the chained handoff:
  `Client Brief` $\rightarrow$ `Requirement Analyst Agent` $\rightarrow$ `Project Planner Agent` $\rightarrow$ `Proposal & Estimation Agent` $\rightarrow$ `Client Communication Agent`.

### Step 4: Model Context Protocol (MCP) Live Host
- **Current State**: GitHub integration is implemented via native `httpx` tool calls in the Tool Registry.
- **Action**: Expose or consume external tools via standard Anthropic/Model Context Protocol (MCP) server endpoints, enabling arbitrary local tool extensions.

### Step 5: External Calendar & Email Connectors
- **Current State**: Draft messages and deadline reminders are stored internally within the workspace.
- **Action**: Integrate Google Calendar API (bidirectional sync of task deadlines) and SMTP/OAuth email sending (with human approval gate).

---

## 6. Project Directory Quick Reference

```
TaskMateAI/
├── apps/
│   ├── api/                      # FastAPI Backend Application
│   │   ├── app/
│   │   │   ├── agent/            # Sprint 3: Bounded Agent, Tool Registry, Permissions
│   │   │   ├── ai/               # Sprint 2 & 4: LLM Providers, Prompts, Extractors
│   │   │   ├── api/routes/       # REST API Endpoints (auth, tasks, requirements, agent)
│   │   │   ├── core/             # Configuration, Logging, Security, Encryption
│   │   │   ├── db/               # Database Engine & Base
│   │   │   ├── integrations/     # External Integrations (GitHub Client)
│   │   │   ├── models/           # SQLAlchemy 2.0 ORM Models
│   │   │   ├── repositories/     # Data Access Layer (Strict Tenant Scoping)
│   │   │   ├── schemas/          # Pydantic v2 Validation Schemas
│   │   │   └── services/         # Domain Services (Business Logic)
│   │   ├── alembic/              # Database Migrations (001 - 005)
│   │   └── tests/                # 103 Automated Pytest Tests
│   └── web/                      # Next.js 14 Web Application
│       ├── app/                  # App Router Pages (dashboard, tasks, requirements, etc.)
│       ├── components/           # Reusable UI Components
│       └── lib/                  # API Client, AuthContext, Types
├── docs/                         # Architecture, API, and Audit Documentation
├── everything you need to know/  # Core Orientation & Research Documentation
├── scripts/                      # Setup & Database Seeding Scripts (seed.py)
├── docker-compose.yml            # Multi-Container Deployment Config
├── Makefile                      # Standard Developer Commands
└── .env.example                  # Environment Configuration Template
```


---

## 7. V1 Specification Gap Analysis — What Remains to Achieve Full Alignment

This section documents the **six areas** where the current codebase (Sprint 0–4 complete) does not yet fully satisfy the Complete V1 Project Context Specification. These gaps represent the prioritized backlog for the next development phase.

> **Note**: The core developer-freelancer loop (CRM → Projects → Tasks → AI Agent → Requirements → GitHub) is **100% functional** and verified. The gaps below are enhancements that expand the automation pipeline toward the final V1 vision.

---

### Gap 1: Proposal & Estimation Module — 0% Complete

**What the V1 Spec requires:**
- A Proposal generator converting approved requirements into a formal Scope of Work (SOW).
- Automated effort estimation (hours/days) per requirement or task group.
- A proposal review UI at `/proposals`.
- An Estimation Agent producing line-item cost breakdowns.

**What exists:** Nothing. No `proposals` table, no estimation logic, no SOW generator, no `/proposals` route.

**What needs to be built:**
- DB model: `proposals` (id, project_id, user_id, status, total_estimate_hours, body_markdown, created_at)
- DB model: `proposal_items` (id, proposal_id, requirement_id, label, estimated_hours, notes)
- Alembic migration: `006_proposals.py`
- Service: `ProposalService` at `apps/api/app/services/proposal.py`
- API routes: `POST /api/v1/projects/{id}/proposals`, `GET /api/v1/projects/{id}/proposals`
- Frontend page: `apps/web/app/projects/[id]/proposals/page.tsx`

---

### Gap 2: Client Communication & Follow-up Agent — 15% Complete

**What the V1 Spec requires:**
- Outbound message drafting engine composing client-facing updates in the developer's voice.
- Follow-up scheduler detecting unanswered requests and auto-drafting follow-up messages.
- A "send for review" UI where the developer approves before sending.

**What exists:** `client_requests` table and `ClientRequestService` store inbound briefs (15% done). No outbound drafting, no follow-up scheduler, no approval UI.

**What needs to be built:**
- DB model: `client_communications` (id, client_id, project_id, direction, subject, body_draft, status, sent_at)
- DB model: `client_follow_ups` (id, client_id, scheduled_at, trigger_reason, status)
- Service: `ClientCommunicationService` with AI-powered draft generation.
- Agent prompt: follow-up detection scanning overdue `client_requests`.
- Frontend: message approval UI at `/clients/[id]/communications`.

---

### Gap 3: Project Milestones & Task Dependencies — 75% Complete

**What the V1 Spec requires:**
- Milestones grouping sets of tasks into deliverable phases.
- Task dependency links (`BLOCKED_BY`, `DEPENDS_ON`) modeling prerequisites.
- Milestone/dependency view on the project detail page.

**What exists:** Tasks with priorities, statuses, and due dates (75% done). No `milestones` table, no `task_dependencies` link table. Tasks are flat.

**What needs to be built:**
- DB model: `milestones` (id, project_id, name, due_date, status)
- DB model: `task_dependencies` (id, task_id, depends_on_task_id, dependency_type)
- New Alembic migration for both tables.
- Service: `MilestoneService` at `apps/api/app/services/milestone.py`
- API routes: `POST /api/v1/projects/{id}/milestones`, `GET /api/v1/projects/{id}/milestones`
- Frontend: milestone grouping panel on the project detail page.

---

### Gap 4: Agent Observability Cockpit UI — 50% Complete

**What the V1 Spec requires:**
- A frontend trace inspector showing agent executions: status, step-by-step tool calls, inputs, outputs, latency, and token usage.
- Real-time or polling-based status updates during active executions.

**What exists:** `agent_executions` and `agent_execution_steps` DB tables, repository, and service are fully implemented. No frontend trace inspector — the assistant page shows conversation output but not the structured execution trace.

**What needs to be built:**
- Frontend page: `apps/web/app/assistant/executions/[id]/page.tsx` with execution step trace.
- API endpoint: `GET /api/v1/agent/executions/{id}` returning full trace + steps.
- Polling or SSE hook in the frontend for live step updates.

---

### Gap 5: Multi-Agent Handoff Pipeline — Not Chained

**What the V1 Spec requires:**
- A coordinated pipeline: `Client Brief → Requirement Analyst → Project Planner → Proposal Agent → Communication Agent`.
- A `WorkflowCoordinator` orchestrating this sequentially with human approval gates between stages.

**What exists:** `RequirementsAnalyzer` (Sprint 4) and `AgentOrchestrator` (Sprint 3) work as robust standalone pipelines. They are **not chained**. Developers manually navigate Requirements → Generate Tasks → Agent.

**What needs to be built:**
- Class: `WorkflowCoordinator` at `apps/api/app/agent/coordinator.py`
  - Method: `async def run_brief_to_plan_pipeline(brief, project, user)` chaining Requirement Analyst → Task Generator → Proposal Agent.
- API route: `POST /api/v1/workflows/brief-to-plan`
- Human-in-the-loop approval checkpoints between each stage.

---

### Gap 6: MCP Adapter Layer — 30% Complete

**What the V1 Spec requires:**
- Standard Model Context Protocol (MCP) adapter so external tools plug into TaskMate without custom integration code.
- An `MCPClientManager` connecting to any MCP-compatible tool server.
- A settings UI for registering custom MCP tool endpoint URLs.

**What exists:** GitHub integration uses native `httpx` calls baked into `github_tools.py` (the pattern exists but is not MCP-standard). No MCP protocol-level client, no dynamic tool registration.

**What needs to be built:**
- Class: `MCPClientManager` at `apps/api/app/integrations/mcp/client.py` implementing MCP JSON-RPC tool discovery and invocation.
- Dynamic tool registration from MCP manifest at application startup.
- Frontend settings page for registering MCP server URLs.

---

### Prioritized Action Plan

| Phase | Focus Area | Status | Priority | Est. Effort |
|---|---|---|---|---|
| **Phase A** | Agent Observability UI (Gap 4) | Backend done, UI missing | HIGH | 1–2 days |
| **Phase B** | Milestones & Task Dependencies (Gap 3) | 75% done | HIGH | 2–3 days |
| **Phase C** | Multi-Agent Handoff Pipeline (Gap 5) | Architecture upgrade needed | MEDIUM | 3–4 days |
| **Phase D** | Client Communication Agent (Gap 2) | 15% done | MEDIUM | 3–4 days |
| **Phase E** | Proposal & Estimation Module (Gap 1) | 0% done | MEDIUM | 4–5 days |
| **Phase F** | MCP Adapter Layer (Gap 6) | 30% done | LOW | 5–7 days |

**Recommendation**: Start with **Phase A** — Agent Observability UI. The backend is fully built (`agent_executions` + `agent_execution_steps` tables, `AgentExecutionRepository`, and `AgentExecutionService` all exist). Only a new GET endpoint and a frontend trace page are needed. This immediately unlocks full debugging visibility for all agent operations.
