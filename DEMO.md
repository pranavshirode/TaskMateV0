# TaskMate AI: Faculty Demo Guide

_State after Sprint 6 (final pre-demo sprint), verified 2026-10-14._

This file covers:
1. what works (and how it was verified);
2. how to run the 10-minute demo;
3. how to add your **manually fine-tuned model** to the AI orchestration;
4. a ready-to-paste **Google Colab prompt** for training that model.

---

## 1. What works (verified)

Everything in the table below was executed, not just read.

**How it was checked:**
- Backend test suite: **178 tests passing**. Ruff, format and mypy are clean.
- Frontend: 10 tests pass, the production build succeeds, and Prettier and ESLint report no errors.
- Database: all 7 migrations apply, roll back and re-apply on **PostgreSQL 16** and SQLite, with no drift from the models.
- A full browser walkthrough of the demo flow below was run against the API on PostgreSQL. All 17 pages loaded with zero errors.

| Area | What you can show | Notes |
|---|---|---|
| Accounts | Register (signs you straight in), login, demo-account button in development | Duplicate emails are matched regardless of letter case |
| Today dashboard | Overdue / due today / high-priority counts, one-click complete with Undo, quick add, project progress bars | All from the database, no hard-coded numbers |
| Tasks | List and Board (drag between columns), live search, filters, inline status, task detail with activity history | |
| Projects & clients | Create, view, progress, linked repositories | |
| Command palette | `Ctrl/⌘ + K` to search and jump; `C` for a new task anywhere | |
| **Requirements analysis** | Paste a client brief → requirements, clarification questions, assumptions, risks → approve → generate task plan → create tasks with traceability | Every requirement is labelled **Client stated** or **AI suggested**. Nothing is invented: a vague brief yields **questions, not fake requirements**. AI failures are reported, not hidden |
| Approval gates | Tasks can only be created from an **approved** analysis (otherwise 409) | Enforced in the backend, not just the UI |
| AI chat | "Create a high priority task to … due tomorrow" creates a real task | Asks *"What should the task be called?"* instead of inventing a title. Ambiguous references ("the login bug" when there are two) get a question |
| **AI agent + approval** | Agent mode: "Create a task to …" → **Needs your approval** card → Approve → task is created **exactly once** (a second approval returns 409). Reject = nothing written | Execution trace at `GET /api/v1/agent/executions/{id}` |
| Project memory, client requests, daily summary | Available on the project page | |
| Security | Per-user data isolation (checked with two users on every resource), refuses the default `SECRET_KEY` in production, no client data in logs by default | |

### Known limitations (say these honestly if asked)

- **Not built:** proposals and estimates, milestones and task dependencies, outbound client messages and follow-ups, and a true multi-agent pipeline. There is one tool-using agent plus a requirements pipeline.
- **Agent approvals:** after you approve, the agent performs that one action and reports the result. It does not continue a longer multi-step plan afterwards.
- **Not tested end to end:** a real OpenAI key and the GitHub OAuth login. The OpenAI tool-calling code is unit-tested with a fake client only.
- **Docker:** the images were not built during verification, because there was no Docker access on the test machine. Run `make up` once yourself before the demo.
- **Offline mode:** with `AI_PROVIDER=mock`, chat understands a limited set of phrasings (create, complete, change status or priority, find, today, overdue). The agent can only create and find tasks. The requirements analysis is keyword-based. **Use a real API key for the demo if you can.**
- **The fine-tuned model is not in the repo yet.** That is your workstream (§3–4).

---

## 2. Running the demo

**One command** (from the repo root, Linux/macOS):

```bash
./hitme.sh          # or: make hitme
```

It creates the Python virtualenv, installs dependencies (only when they've changed), creates `apps/api/.env` if missing (SQLite, offline AI, random `SECRET_KEY`), migrates the database (backing up an older SQLite file first), seeds the demo user, and starts the API and the web app. If port 8000 or 3000 is busy it picks the next free port and wires both sides together. `Ctrl+C` stops both. Options: `--setup`, `--no-seed`, `--api-port N`, `--web-port N`.

For the full assistant, set `AI_PROVIDER=openai` and `AI_API_KEY=...` in `apps/api/.env`.

<details><summary>Manual steps (what the script does)</summary>

```bash
# Terminal 1: backend
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# apps/api/.env needs: DATABASE_URL=sqlite+aiosqlite:///./taskmate.db  SECRET_KEY=<openssl rand -hex 32>
#                      AI_PROVIDER=openai + AI_API_KEY=...   (or AI_PROVIDER=mock for offline)
alembic upgrade head
python scripts/seed_db.py            # demo user alex@taskmate.dev / password123
uvicorn app.main:app --port 8000

# Terminal 2: frontend
cd apps/web && npm ci && npm run dev  # http://localhost:3000
```

</details>

### 10-minute script

1. **Login** with *Use demo account*. The Today page shows a summary sentence, counts, and the focus list. Tick a task done, then click **Undo** in the toast.
2. **Tasks → Board**: drag a card to *In review*. Press `Ctrl+K`, type "api", and jump to a task.
3. **Requirements**: open a project → Requirements → new analysis. Paste:
   > *Patients should book appointments with doctors and log in with Google. Payments via Stripe. It must be fast.*

   **Analyze**. Point out:
   - **Client stated** vs **AI suggested** badges;
   - a clarification question about what "fast" means, instead of an invented "300 ms" target;
   - no invented iOS or PCI requirements.

   Then paste just **"hello"** as a brief. There are no requirements, only a question asking what the system should do. *This is the anti-hallucination guarantee.*
4. Try **Generate Task Plan → approve tasks** before approving the analysis. It is refused (*Approve the requirements analysis first*). Approve, then create the tasks. They appear with requirement traceability.
5. **AI Assistant → Agent**: *"Create a high priority task to send the clinic proposal due tomorrow"*. The **Needs your approval** card appears. **Approve**. "Done", and the task appears on Today and Tasks. Mention that a second approval is rejected (no duplicate actions).
6. **Chat**: *"Create a task"* gets *"What should the task be called?"* (no fake data).
7. **Your fine-tuned model** (once integrated, §3): show the chat reply metadata *Intent classified by the fine-tuned model (97%)*, then your metrics and confusion matrix.

---

## 3. Adding your manually fine-tuned model to the orchestration

### 3.1 Which model, and why

**Fine-tune an intent classifier.** It is the easiest component of the orchestration to replace with your own model:
- **Simple task:** single-label text classification of one short message.
- **Labels already exist:** the 11 values of `IntentType` in `apps/api/app/ai/schemas/intent.py`.
- **Starter data exists:** `apps/api/evaluation/dataset.json` (100 examples; 50 are the unused label `RUN_AGENT`) and `apps/api/tests/evaluation/eval_dataset.json` (35 examples). You will need to add more (§4).
- **Cheap to train:** `distilbert-base-uncased` trains in minutes on a free Colab T4, and runs on CPU at about 10–30 ms per message.
- **Clear integration point:** a few lines in one function.

**Labels:** `GENERAL_QUESTION`, `CREATE_TASK`, `UPDATE_TASK`, `COMPLETE_TASK`, `CHANGE_TASK_STATUS`, `CHANGE_TASK_PRIORITY`, `SEARCH_TASKS`, `GET_TODAY_TASKS`, `GET_OVERDUE_TASKS`, `GET_PROJECT_INFO`, `GET_CLIENT_INFO`.

> ⚠️ Confirm with your faculty that a fine-tuned *classifier* satisfies the "trained/fine-tuned model" requirement (see `everything you need to know/YourSide.md` §2). If they require a *generative* fine-tune, this plan changes.

### 3.2 Where it plugs in

Request flow for `POST /api/v1/ai/chat` (`apps/api/app/ai/services/orchestrator.py`, `AIOrchestrator.chat`):

```
user message ─► LLM (intent + entities JSON) ─► step 6: parse ─► [NEW] fine-tuned classifier decides the intent
                                                                   (LLM keeps extracting title/date/priority)
             ─► entity resolution ─► clarification checks ─► domain services (create/update/search tasks)
```

**The fine-tuned model decides *what the user wants*. The LLM only extracts *the details*.** If the model is missing or unsure, the app falls back to the LLM's intent, so the demo never breaks.

### 3.3 Steps

**1. Put the artifacts in place.** Unzip the Colab output so this folder exists. Don't commit large weights to Git; use Git LFS, the Hugging Face Hub or Google Drive, and note the version.

```
apps/api/models/intent-classifier/
    config.json  model.safetensors  tokenizer.json  tokenizer_config.json  vocab.txt  special_tokens_map.json
    label_map.json  metrics.json  MODEL_CARD.md
```

Add `apps/api/models/` to `.gitignore` unless you use LFS.

**2. Install the inference dependencies** (CPU only):

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install "transformers>=4.44"
```

Add them as an optional extra in `apps/api/pyproject.toml`:

```toml
ml = ["transformers>=4.44", "torch>=2.2"]
```

**3. Add the settings** in `apps/api/app/core/config.py` (inside `Settings`), and document them in `.env.example`:

```python
INTENT_MODEL_PATH: str = ""              # e.g. "models/intent-classifier"; empty = disabled
INTENT_MODEL_MIN_CONFIDENCE: float = 0.6 # below this, the LLM's intent is used
```

**4. Create `apps/api/app/ai/intent_classifier.py`:**

```python
"""Fine-tuned intent classifier (team-trained DistilBERT). Optional: the app works without it."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class IntentPrediction:
    label: str
    confidence: float
    model_version: str


class IntentClassifier:
    def __init__(self, path: str):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # optional dependency

        self.path = Path(path)
        self.tokenizer = AutoTokenizer.from_pretrained(self.path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.path).eval()
        self.id2label = {int(k): v for k, v in json.loads((self.path / "label_map.json").read_text()).items()}
        card = self.path / "metrics.json"
        self.version = json.loads(card.read_text()).get("model_version", "unknown") if card.exists() else "unknown"

    def predict(self, text: str) -> IntentPrediction:
        import torch

        inputs = self.tokenizer(text[:512], return_tensors="pt", truncation=True, max_length=64)
        with torch.no_grad():
            probs = self.model(**inputs).logits.softmax(dim=-1)[0]
        idx = int(probs.argmax())
        return IntentPrediction(self.id2label[idx], float(probs[idx]), self.version)


@lru_cache
def get_intent_classifier() -> IntentClassifier | None:
    """Loaded once. Returns None (feature off) if unset or unloadable, so the app never crashes over it."""
    path = get_settings().INTENT_MODEL_PATH
    if not path:
        return None
    try:
        return IntentClassifier(path)
    except Exception:
        logger.exception("Intent classifier could not be loaded from %s; using the LLM intent", path)
        return None
```

**5. Hook it into the orchestrator.** In `AIOrchestrator.chat`, directly **after** the step-6 `try/except` block that sets `intent_val`, `confidence`, `entities` and `reply`, add:

```python
        # 6b. Team fine-tuned intent classifier decides the intent (LLM still extracts the entities).
        intent_source = "llm"
        classifier = get_intent_classifier()
        if classifier is not None:
            try:
                prediction = classifier.predict(message)
                if prediction.confidence >= get_settings().INTENT_MODEL_MIN_CONFIDENCE:
                    intent_val, confidence = prediction.label, prediction.confidence
                    intent_source = f"fine-tuned:{prediction.model_version}"
            except Exception:
                logger.exception("Intent classifier failed; keeping the LLM intent")
```

with these imports at the top of the file (skip any that are already there):

```python
from app.ai.intent_classifier import get_intent_classifier
from app.core.config import get_settings
```

Then make it visible as evidence:
- Add `intent_source: str | None = None` to `AIChatResponse` in `app/ai/schemas/responses.py`.
- Pass `intent_source=intent_source` in the final `return AIChatResponse(...)` of `chat`.
- In the frontend, `components/ai/AssistantChat.tsx` → `MessageBubble`: show it under assistant replies, e.g. *"Intent: CREATE_TASK · fine-tuned model · 97%"*. The `Message` type already has `intent` and `confidence`. Add `intentSource`, and add `intent_source?: string` to `AIChatResponse` in `lib/api-client.ts`.

**6. Configure and run.** Set `INTENT_MODEL_PATH=models/intent-classifier` in `apps/api/.env` and restart the API.

**7. Add tests** (`apps/api/tests/test_intent_classifier.py`). Graders look for these:
- monkeypatch `get_intent_classifier` to return a stub with fixed predictions. Assert that a high-confidence prediction overrides the LLM's intent and sets `intent_source` to `fine-tuned:…`, and that a low-confidence one does not;
- assert that the app still answers when the classifier raises an exception;
- optionally, a slow test (skipped when the folder is missing) that loads the real model and checks 5 known messages.

**8. Evidence pack for the faculty:**
- the Colab notebook;
- the training logs;
- `metrics.json`, comparing the baseline against the fine-tuned model;
- the confusion matrix PNG;
- `MODEL_CARD.md`;
- the dataset with a provenance note;
- the integration diff above;
- the test output;
- a screenshot of the chat showing *fine-tuned model*.

---

## 4. Google Colab prompt (copy-paste into Gemini in Colab)

Before pasting, set **Runtime → Change runtime type → T4 GPU**, and upload these files to the Colab file panel:
- `apps/api/evaluation/dataset.json`;
- `apps/api/tests/evaluation/eval_dataset.json`;
- your team's extra labelled file `extra_intents.csv` (columns `text,label`, roughly 80 examples per label, written and checked by you).

Then paste:

```text
You are helping me fine-tune a text classifier for my final-year project "TaskMate AI". Write and run a complete,
well-commented Colab notebook, one step per cell, explaining each step briefly. Do not skip evaluation.

GOAL
Fine-tune `distilbert-base-uncased` to classify a user's chat message into exactly one intent label:
GENERAL_QUESTION, CREATE_TASK, UPDATE_TASK, COMPLETE_TASK, CHANGE_TASK_STATUS, CHANGE_TASK_PRIORITY,
SEARCH_TASKS, GET_TODAY_TASKS, GET_OVERDUE_TASKS, GET_PROJECT_INFO, GET_CLIENT_INFO.
Definitions: COMPLETE_TASK = mark a task done/finished; CHANGE_TASK_STATUS = any other status change (in progress,
blocked, review, back to todo); UPDATE_TASK = change title/description/due date; GENERAL_QUESTION = anything else.

DATA
1. Load the uploaded files:
   - dataset.json: list of objects; text in "message", label in "expected_intent".
   - eval_dataset.json: list of objects; text in "prompt", label in "expected_intent".
   - extra_intents.csv: columns text,label (written and checked by our team).
   Drop rows whose label is not in the 11 labels above (e.g. RUN_AGENT, UNKNOWN). Strip whitespace,
   drop empty texts, and drop exact duplicate texts (case-insensitive). Print the count per label as a table.
2. If any label has fewer than 40 examples, STOP and print which labels need more data. Do not generate
   synthetic data automatically; we will write more examples ourselves.
3. Split into train/validation/test = 70/15/15, stratified by label, random_state=42. Print sizes per split.

BASELINE (needed to show fine-tuning helps)
4. Train TF-IDF (word 1-2 grams) + LogisticRegression(max_iter=1000) on train; report accuracy, macro-F1,
   and a per-class classification_report on the TEST set.

FINE-TUNING
5. Use Hugging Face transformers + datasets. Tokenize with max_length=64, padding, truncation.
   Set seeds (random, numpy, torch, transformers.set_seed) to 42 and print library versions.
6. AutoModelForSequenceClassification with num_labels=11 and id2label/label2id mappings.
   TrainingArguments: learning_rate=5e-5, per_device_train_batch_size=16, per_device_eval_batch_size=32,
   num_train_epochs=5, weight_decay=0.01, evaluation and save strategy "epoch", load_best_model_at_end=True,
   metric_for_best_model="macro_f1", fp16=True if a GPU is available, logging every 10 steps, report_to="none".
   Use compute_metrics returning accuracy and macro_f1 (sklearn f1_score average="macro").
7. Train and show the training/validation loss and metrics per epoch.

EVALUATION
8. On the TEST set: accuracy, macro-F1, weighted-F1, per-class classification_report, and a confusion matrix
   plotted with matplotlib (labels on both axes, saved as confusion_matrix.png).
9. Print a comparison table: baseline vs fine-tuned (accuracy, macro-F1).
10. List the 15 test examples the model got wrong with true label, predicted label and confidence.
11. Measure average CPU inference time per message on 100 messages (move the model to CPU for this).

EXPORT (this folder is loaded by our app)
12. Save to ./intent-classifier/ :
    - model + tokenizer via save_pretrained (safetensors),
    - label_map.json mapping index (as string) -> label, e.g. {"0": "CREATE_TASK", ...},
    - metrics.json with: model_version (e.g. "intent-distilbert-v1-<date>"), base_model, dataset sizes per split,
      label counts, hyperparameters, seed, library versions, baseline metrics, fine-tuned test metrics,
      avg_cpu_latency_ms,
    - confusion_matrix.png,
    - MODEL_CARD.md: intended use, labels with definitions, data sources and how they were labelled,
      training setup, results table, known limitations, and example mistakes.
13. Write a predict(text) function that loads ./intent-classifier and returns (label, confidence); demo it on:
    "Create a high priority task to fix the login bug due tomorrow", "What's overdue?",
    "Mark the payment task as done", "Move the API docs task to blocked", "Who is the client for Acme?".
14. Zip ./intent-classifier into intent-classifier.zip and download it with google.colab.files.download.

RULES
- Never invent or hard-code metrics; report only what the code computes.
- Keep the test set untouched until step 8.
- If a step fails, explain the error and fix it before continuing.
```

### After Colab

1. Unzip `intent-classifier.zip` into `apps/api/models/intent-classifier/`.
2. Follow §3.3 steps 2–7.
3. Run the API and send *"Mark the login task as done"*. The reply metadata should say **fine-tuned model**.
4. Record every metric exactly as Colab printed it. If fine-tuning does not beat the baseline, say so: that is still a valid, honest result.
