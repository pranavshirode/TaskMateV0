# AI Provider Configuration & Verification Guide

This guide describes how to configure and verify AI providers in TaskMate AI, ranging from the built-in deterministic Mock provider (for offline testing & CI) to live external LLMs (OpenAI, Google Gemini, Ollama, LM Studio).

---

## 1. Supported Providers

| Provider | `AI_PROVIDER` value | Requirements | Notes |
|---|---|---|---|
| **Mock (Default)** | `mock` | None | Fully deterministic rule-based engine. Supports requirements analysis, task planning, proposal generation, and client communications offline. |
| **OpenAI** | `openai` | `AI_API_KEY=sk-...` | Direct OpenAI API access (`gpt-4o-mini`, `gpt-4o`, etc.). |
| **Google Gemini** | `openai` | `AI_API_KEY=AIza...`<br>`AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`<br>`AI_MODEL=gemini-2.5-flash` | Uses OpenAI-compatible endpoints provided by Google AI Studio. |
| **Ollama (Local)** | `ollama` or `local` | Ollama running on `http://localhost:11434`<br>`AI_MODEL=taskmate-srs` or `mistral` | Local inference with zero external network traffic. |
| **LM Studio** | `lmstudio` | LM Studio local server on `http://localhost:1234/v1` | Local OpenAI-compatible server. |

---

## 2. Verification Utility

Run the verification script anytime using the backend virtual environment:

```bash
apps/api/.venv/bin/python scripts/ai_check.py
```

### What It Tests
1. **Model & Endpoint Resolution:** Validates that settings correctly resolve the configured provider, model, base URL, and credentials.
2. **Health Check:** Contacts the provider endpoint to check service reachability.
3. **Text Completion:** Sends a test ping prompt and verifies token accounting, latency, and response generation.
4. **Structured JSON Output:** Tests schema-compliant JSON generation (`response_format={"type": "json_object"}`).

---

## 3. Configuration Examples

### A. Google Gemini via OpenAI Compatibility
In `.env`:
```env
AI_PROVIDER=openai
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
AI_MODEL=gemini-2.5-flash
AI_API_KEY=AIzaSy...your_gemini_api_key
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=2048
```

### B. Standard OpenAI
In `.env`:
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_API_KEY=sk-proj-...your_openai_key
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=2048
```

### C. Local Ollama Fine-Tuned Model
In `.env`:
```env
AI_PROVIDER=ollama
AI_BASE_URL=http://localhost:11434/v1
AI_MODEL=taskmate-srs:latest
AI_API_KEY=local-key
```

---

## 4. Safety Guardrails & Invariants

TaskMate AI enforces strict boundaries regardless of the provider:
- **Approval Gating:** Write tools and external client communications cannot be dispatched automatically by the model. Internal drafts require developer approval.
- **Credential Isolation:** API keys and encryption tokens are never passed into model prompts.
- **Graceful Fallback:** If an external provider is unreachable or returns invalid JSON, TaskMate surfaces informative errors rather than crashing or corrupting data.

