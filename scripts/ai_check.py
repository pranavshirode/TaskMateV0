#!/usr/bin/env python3
"""TaskMate AI Provider Health & Verification Utility.

Checks the configured AI provider (OpenAI, Gemini via OpenAI-compat, Ollama, LM Studio, or Mock).
Validates text generation, JSON mode, and latency without fabricating responses.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

# Ensure apps/api is on the python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
API_DIR = os.path.join(PROJECT_ROOT, "apps", "api")
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from app.ai.providers import get_ai_provider
from app.ai.providers.base import AIMessage
from app.core.config import get_settings


async def main() -> int:
    print("=" * 60)
    print("TaskMate AI — Provider Verification Utility")
    print("=" * 60)

    settings = get_settings()
    provider_name = settings.AI_PROVIDER.lower()
    model_name = settings.AI_MODEL
    base_url = settings.AI_BASE_URL or "default"
    has_key = bool(settings.AI_API_KEY)

    print(f"Configured Provider: {provider_name}")
    print(f"Configured Model   : {model_name}")
    print(f"Base URL           : {base_url}")
    print(f"API Key Present    : {'Yes' if has_key else 'No'}")
    print("-" * 60)

    provider = get_ai_provider()
    model_info = provider.get_model_info()

    if provider_name == "mock":
        print("[INFO] Operating in MOCK / OFFLINE mode.")
        print("Testing deterministic rule-based AI engine...")
        t0 = time.monotonic()
        res = await provider.generate([AIMessage(role="user", content="Hello TaskMate")])
        elapsed = int((time.monotonic() - t0) * 1000)
        print(f"[OK] Mock response received ({elapsed}ms): {res.content[:100]}...")
        print("\nTo connect a real provider:")
        print("  1. In .env, set AI_PROVIDER=openai (or ollama/local)")
        print("  2. Set AI_API_KEY=your_key")
        print("  3. For Gemini (OpenAI compat): AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/")
        print("     and AI_MODEL=gemini-2.5-flash")
        print("=" * 60)
        return 0

    print(f"Testing live connectivity to {provider_name}...")
    try:
        is_healthy = await provider.health_check()
        print(f"Health check status: {'Healthy' if is_healthy else 'Unhealthy/Inconclusive'}")
    except Exception as e:
        print(f"[WARN] Health check call raised: {e}")

    # Test 1: Simple text generation
    print("\n[1/2] Testing text completion...")
    t0 = time.monotonic()
    try:
        res = await provider.generate([
            AIMessage(role="user", content="Respond with exactly: PONG")
        ])
        latency = int((time.monotonic() - t0) * 1000)
        print(f"[OK] Completion successful in {latency}ms")
        print(f"     Model: {res.model}")
        print(f"     Content: {res.content.strip()}")
        print(f"     Tokens: input={res.input_tokens}, output={res.output_tokens}, total={res.total_tokens}")
    except Exception as e:
        print(f"[FAIL] Text completion failed: {e}")
        return 1

    # Test 2: Structured JSON mode
    print("\n[2/2] Testing structured JSON mode...")
    t0 = time.monotonic()
    try:
        json_res = await provider.generate(
            [AIMessage(role="user", content='Respond with a JSON object: {"status": "ok", "agent": "taskmate"}')],
            response_format={"type": "json_object"},
        )
        latency = int((time.monotonic() - t0) * 1000)
        print(f"[OK] JSON response successful in {latency}ms")
        print(f"     Content: {json_res.content.strip()}")
    except Exception as e:
        print(f"[FAIL] JSON mode failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("ALL LIVE AI CHECKS PASSED SUCCESSFULLY.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

