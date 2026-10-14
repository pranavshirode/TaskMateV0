# Everything You Need To Know — TaskMate AI

Welcome to the comprehensive knowledge repository for **TaskMate AI**.

This directory contains the authoritative technical documentation, operational setup guides, academic research formulations, and codebase blueprints. It is designed so that both **human software engineers** and **incoming AI models** can immediately understand, run, extend, and evaluate the project without having to scan every file in the codebase.

---

## Document Index

### Demo: [../DEMO.md](../DEMO.md) — Faculty demo guide (start here)
- What works (verified), the 10-minute demo script, how to add the fine-tuned intent classifier, and the Google Colab training prompt.

### 0. [AUDIT_2026-10-14.md](./AUDIT_2026-10-14.md) — Verified Repository Audit (read first)
- **Purpose**: What was actually run and verified on 2026-10-14: test results, an end-to-end API probe, migration and frontend checks.
- **Key Sections**: Verified state, coverage matrix, defect register (BUG-01…20), trained-model plan, demo risks, sprint plan, and the next implementation prompt.
- **Note**: It supersedes the claims in `docs/AUDIT_REPORT.md` and parts of `context.md` §3.6 (e.g. "103/103 passing").

### 1. [context.md](./context.md) — Project Context, Current State & Strategic Roadmap
- **Purpose**: Understand the mission, background, and evolution of TaskMate AI.
- **Key Sections**:
  - Executive context & philosophy ("AI that executes, not just advises").
  - The complete V1 final goal for freelance developers.
  - Sprint-by-Sprint audit (Sprint 0 through Sprint 4): what was built, verified, and audited.
  - Verified test metrics (103 backend pytest tests passing, Next.js build clean).
  - Concrete next steps for V2 production hardening.
  - **Section 7 — V1 Gap Analysis**: Six remaining work areas with completion percentages, exact models/services to build, and a prioritized Phase A–F action plan.

### 2. [YourSide.md](./YourSide.md) — Developer Action Checklist
- **Purpose**: Actionable checklist of tasks that **only you** (the human developer) can perform.
- **Key Sections**:
  - Environment variables reference with exact file paths (`.env`, `apps/api/.env`, `apps/web/.env.local`).
  - Generating Fernet encryption keys (`GITHUB_ENCRYPTION_KEY`).
  - GitHub OAuth App setup on github.com (step-by-step).
  - Resolving the GitHub PAT `workflow` scope push rejection.
  - Local boot options (Docker Compose vs. SQLite dev mode).
  - Pre-seeded demo credentials (`alex@taskmate.dev` / `password123`).
  - Manual verification checklist.

### 3. [model_orchestration.md](./model_orchestration.md) — Academic Research Paper Formulation
- **Purpose**: Written specifically to support an **academic research paper**, thesis chapter, or conference submission on multi-agent software engineering systems.
- **Key Sections**:
  - Formal mathematical POMDP modeling of the Bounded Agent Loop ($T \le 10$).
  - Mathematical termination proofs and human-in-the-loop authorization gates.
  - End-to-end system architecture with ASCII / Mermaid diagrams.
  - Multi-agent functional specialization roster (Requirement Analyst, Project Planner, Client Communication, Estimation, Monitoring, Documentation).
  - Grounding, zero-fabrication guarantees, and bidirectional requirement-to-task traceability matrix.
  - Empirical verification results across 103 test cases.

### 4. [developer_and_model_guide.md](./developer_and_model_guide.md) — Incoming Model & Developer Blueprint
- **Purpose**: The definitive architectural cheat sheet for any new AI agent or software engineer handed this project.
- **Key Sections**:
  - Complete monorepo directory map with file roles.
  - Full database entity dictionary (20+ SQLAlchemy models, relationships, and foreign keys).
  - Complete Agent Tool Registry catalog (tool names, permissions, schemas, domain services).
  - REST API endpoint catalog and data contracts.
  - Architectural invariants and coding standards (strict tenant scoping, Pydantic validation, safe migrations).
  - Quickstart test and verification commands.
  - **Section 7 — Missing Implementations**: Tables listing every not-yet-implemented model, service, route, and frontend page needed to close the V1 gaps.

---

## Quick Reference Commands

```bash
# 1. Start application with Docker Compose
make up

# 2. Run database migrations to head
make migrate

# 3. Seed demo workspace data
docker compose exec api python scripts/seed.py

# 4. Run full backend test suite
make test-backend

# 5. Build frontend Next.js application
cd apps/web && npm run build
```

