# TaskMate AI — Developer Action Checklist (YourSide.md)

_Last updated 2026-10-14, after Sprint 5 (see [AUDIT_2026-10-14.md](./AUDIT_2026-10-14.md) §9)._

---

## 1. Overview

This file lists the things **only you** (the human team) can do: decisions, accounts, secrets, compute, and demo preparation. An AI coding assistant can write the code, but it can't decide what your faculty will accept, label your dataset, or create your API keys.

> **Demo prep:** read [`/DEMO.md`](../DEMO.md). It covers what works, the 10-minute demo script, how to plug in your fine-tuned model, and the Colab prompt.
>
> **Read §2 first.** Sprint 5 fixed the broken setup commands (`make migrate`, the seed scripts). Section 6 now lists commands verified on 2026-10-14.

---

## 2. Blocking actions (do these first)

| # | Action | Why it blocks | Done |
|---|---|---|---|
| 1 | **Ask your faculty guide exactly what counts as "trained/fine-tuned".** Is a fine-tuned text classifier acceptable, or must it be a generative model (LoRA/PEFT)? What evidence do they want (notebook, metrics, confusion matrix, live demo)? Get it in writing (email). | Decides the whole model workstream. Currently **no model exists** in the repo. | [ ] |
| 2 | **Add the SRS PDF to the repo**, e.g. `docs/SRS.pdf` plus a short `docs/SRS-requirements.md` list of numbered requirements. | Requirement-by-requirement coverage can't be checked without it. | [ ] |
| 3 | **Start labelling data for the model now**, in parallel with the bug fixes (plan in the audit, §4). Agree on the label definitions as a team before labelling. Aim for 800–1,500 labelled requirement sentences, split by brief. | Labelling is human time, not code. It's the slowest part. | [ ] |
| 4 | **Get a runtime LLM API key** (OpenAI, or another provider supported by `AI_PROVIDER`). Set a monthly spend limit on the provider dashboard. | Every AI test so far used the `mock` provider. The real provider path has **never been verified**. | [ ] |
| 5 | **Decide where model weights will live** (Hugging Face Hub private repo, Google Drive, or Git LFS). Don't commit large `.safetensors`/`.bin` files to normal Git. | The app has to load a specific, versioned artifact. | [ ] |

---

## 3. Environment variables and secrets

### 3.1 Files
```bash
cp .env.example .env                                    # repo root: used by Docker Compose
cp apps/web/.env.local.example apps/web/.env.local      # frontend
# Running the API outside Docker: apps/api/.env (it already exists locally and is git-ignored)
```
Never commit real `.env` files. `.gitignore` already covers them. The history scan on 2026-10-14 found no real keys committed.

### 3.2 Reference

| Variable | Required? | Example | Notes |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | output of `openssl rand -hex 32` | Signs login tokens. The API **refuses to start** with the built-in default unless `APP_ENV` is `development` or `testing`. `docker compose` refuses to start without it. |
| `SQL_ECHO` | Optional | `false` | `true` logs every SQL statement with its data (client briefs, emails). Only enable it briefly while debugging. |
| `DATABASE_URL` | **Yes** | `sqlite+aiosqlite:///./taskmate.db` or `postgresql+asyncpg://taskmate:<pw>@localhost:5432/taskmate` | If unset, the default is an in-memory database (data may be lost). |
| `CORS_ORIGINS` | **Yes** | `["http://localhost:3000"]` | Must include the URL the frontend runs on. |
| `AI_PROVIDER` | **Yes** | `openai` or `mock` | `mock` gives deterministic offline answers. Use it for tests, not the demo. |
| `AI_API_KEY` | Yes, unless `mock` | `sk-...` | From your provider's dashboard. |
| `AI_MODEL` | Optional | `gpt-4o-mini` | |
| `AI_BASE_URL` | Optional | | For OpenAI-compatible endpoints. |
| `AGENT_MAX_STEPS` | Optional | `10` | Enforced. |
| `AGENT_MAX_TOOL_CALLS`, `AGENT_MAX_EXECUTION_TIME` | Optional | `10`, `120` | Enforced. A run that hits a limit ends as `TIMEOUT`. |
| `AGENT_REQUIRE_APPROVAL_FOR_WRITES` | Optional | `true` | ⚠️ There is no approve button/endpoint yet (BUG-02), so with `true` the agent can't write. Don't set `false` to work around it for the demo; it removes the safety gate. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`, `GITHUB_ENCRYPTION_KEY` | Optional | | Only for the GitHub integration (§4). Not verified by the audit. |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://localhost:8000` | In `apps/web/.env.local`. |

Generate the GitHub token encryption key with:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 4. GitHub OAuth app (optional, only if you demo GitHub)

1. Go to https://github.com/settings/developers → **New OAuth App**.
2. Fill in:
   - Homepage `http://localhost:3000`
   - Callback `http://localhost:3000/settings/integrations/github/callback`
3. Copy the Client ID into `GITHUB_CLIENT_ID`. Generate a client secret and put it in `GITHUB_CLIENT_SECRET`.
4. Set `GITHUB_ENCRYPTION_KEY` (§3.2).

---

## 5. Pushing to GitHub (the `workflow` scope error)

If `git push` is rejected with *"refusing to allow a Personal Access Token to create or update workflow … without `workflow` scope"*:
1. Go to https://github.com/settings/tokens and edit your token, or create a new one, with the **`repo`** and **`workflow`** scopes.
2. Push normally and paste the token when asked for a password:
   ```bash
   git push origin pranav-branch
   ```
   Don't put the token inside the remote URL; it ends up in your shell history and `.git/config`. Prefer `gh auth login` or your OS keychain credential helper over `credential.helper store`, which saves the token in plain text.

CI (`.github/workflows/ci.yml`) now runs on every push and pull request, on any branch.

---

## 6. Running the project locally

### 6.0 Quickest: one command
```bash
./hitme.sh        # or: make hitme   (Ctrl+C stops everything)
```
This sets up and runs everything below automatically. See `/DEMO.md` §2 for the options.

### 6.1 No Docker, SQLite (verified 2026-10-14)
```bash
# Backend
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# apps/api/.env: DATABASE_URL=sqlite+aiosqlite:///./taskmate.db, AI_PROVIDER=mock (or openai + key), SECRET_KEY=...

alembic upgrade head               # fixed in Sprint 5 (verified on SQLite and PostgreSQL 16)
python scripts/seed_db.py          # demo data; `python scripts/seed.py` from the repo root also works
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd apps/web
npm ci
npm run dev                        # http://localhost:3000
```

### 6.2 Docker Compose
```bash
# .env must contain SECRET_KEY (compose refuses to start without it)
make up
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_db.py
```
The migrations and the seed were verified against PostgreSQL 16 directly. **The Docker images themselves weren't built in the audit** (no Docker access on that machine), so do one `make up` run yourself and tick it off in §8.

### 6.3 Demo login
`scripts/seed.py` creates the user `alex@taskmate.dev` / `password123`. It also creates clients and projects: *Acme SaaS Dashboard*, *Acme Mobile App*, *ByteForge API*, and their tasks. In development, the login page also has a **Use demo account** button.

### 6.4 Running the checks
```bash
cd apps/api && pytest -q && ruff check . && mypy app/   # 158 passed; lint and types clean (2026-10-14)
cd apps/web && npx jest && npm run lint && npm run build     # currently all pass
```

---

## 7. Model training workstream (your side)

The code integration can be done by an assistant. These parts are yours:
- [ ] Faculty confirmation (§2 item 1).
- [ ] Annotation guide: label definitions, edge cases, 10 worked examples per label.
- [ ] Data collection and licensing notes. Record where every example came from. Use only data you're allowed to use.
- [ ] Labelling. Have two people label the same 100 examples and report agreement.
- [ ] Training run on Google Colab using the ready-made prompt in `/DEMO.md` §4 (DistilBERT intent classifier, free T4). Save the notebook, logs, seed and hyperparameters.
- [ ] Integrate it using `/DEMO.md` §3.3 (about 40 lines of code and 3 tests).
- [ ] Keep the evaluation evidence: baseline vs fine-tuned, per-label precision/recall/F1, macro F1, confusion matrix, 10 representative mistakes.
- [ ] Upload the artifacts (weights, tokenizer, label map, config) to the storage chosen in §2 item 5, and record the version/hash.

Never write down numbers you didn't actually measure.

---

## 8. Pre-demo checklist

- [x] Sprint 5 fixes done: `pytest` fully green, migrations work (audit §9). Still to do: commit and push them.
- [ ] `make up` builds and runs on your machine with Docker.
- [ ] **Fresh-machine rehearsal**: clone → setup per §6 → seed → log in, on a machine that has never run the project.
- [ ] `curl http://localhost:8000/health/ready` returns `"database": "connected"`.
- [ ] With a **real** `AI_API_KEY`:
  - [ ] a chat message gets a reply;
  - [ ] "Create a task to … due tomorrow" creates a task you can see on the Tasks page.
- [ ] Requirements flow: Requirements → New analysis → paste a brief → Analyze → answer a question → **Approve** → Generate tasks → tasks appear with requirement links.
  - [ ] Also paste an **unrelated, short brief** and confirm no made-up requirements appear (BUG-05 must be fixed first).
- [ ] The trained model's output is visible in the analysis, and you can explain its metrics.
- [ ] Agent mode with a **real** API key: a read request ("what's overdue?") gets an answer. Agent **writes** still need Sprint 7 (BUG-02, the approval flow).
- [ ] Nothing in the demo is hard-coded or fake. Every number on screen comes from the database or a real model run.
