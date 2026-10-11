#!/usr/bin/env python3
"""AI evaluation script for TaskMate Sprint 2.

Runs the evaluation dataset against the AI system and measures:
- Intent accuracy: Does the AI detect the correct intent?
- Entity extraction accuracy: Are the right entities extracted?
- Overall metrics and baseline recording.

Usage:
    python -m evaluation.evaluate
    # or via Makefile:
    make evaluate-ai

Requires:
    - AI_API_KEY environment variable set
    - Access to the configured AI provider
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.providers.base import AIMessage, MessageRole
from app.ai.providers.factory import create_ai_provider, reset_ai_provider
from app.ai.prompts.system import SYSTEM_PROMPT
from app.core.config import Settings


def load_dataset() -> list[dict[str, Any]]:
    """Load the evaluation dataset."""
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


def create_test_settings() -> Settings:
    """Create settings for evaluation."""
    return Settings(
        AI_API_KEY=os.environ.get("AI_API_KEY", ""),
        AI_PROVIDER=os.environ.get("AI_PROVIDER", "openai"),
        AI_MODEL=os.environ.get("AI_MODEL", "gpt-4o-mini"),
    )


async def evaluate_single(
    provider, message: str, expected_intent: str,
) -> dict[str, Any]:
    """Evaluate a single test case."""
    system_content = SYSTEM_PROMPT.render(
        current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        user_name="Test Developer",
        workspace_context="Active Projects: Acme Website, Client Portal, Mobile App\nClients: Acme Inc, Beta Corp\nRecent Tasks: Fix login bug (HIGH, TODO), Update API docs (MEDIUM, IN_PROGRESS), Add auth (HIGH, TODO)",
    )

    messages = [
        AIMessage(role=MessageRole.SYSTEM, content=system_content),
        AIMessage(role=MessageRole.USER, content=message),
    ]

    start = time.monotonic()
    try:
        response = await provider.generate(
            messages,
            response_format={"type": "json_object"},
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        # Parse response
        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON response",
                "latency_ms": latency_ms,
                "tokens": response.usage.total_tokens,
            }

        detected_intent = parsed.get("intent", "")
        intent_correct = detected_intent.upper() == expected_intent.upper()

        return {
            "success": True,
            "intent_correct": intent_correct,
            "detected_intent": detected_intent,
            "entities": parsed.get("entities", {}),
            "confidence": parsed.get("confidence", 0),
            "latency_ms": latency_ms,
            "tokens": response.usage.total_tokens,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(type(e).__name__),
            "latency_ms": int((time.monotonic() - start) * 1000),
            "tokens": 0,
        }


def check_entity_match(
    expected: dict[str, Any], actual: dict[str, Any]
) -> dict[str, bool]:
    """Check which expected entities were correctly extracted."""
    results = {}
    for key, expected_value in expected.items():
        if expected_value is None:
            continue
        actual_value = actual.get(key)
        if actual_value is None:
            results[key] = False
        elif isinstance(expected_value, str):
            results[key] = expected_value.lower() in str(actual_value).lower()
        else:
            results[key] = actual_value == expected_value
    return results


async def run_evaluation() -> dict[str, Any]:
    """Run the complete evaluation suite."""
    dataset = load_dataset()
    settings = create_test_settings()

    if not settings.AI_API_KEY:
        print("ERROR: AI_API_KEY environment variable is required")
        print("Set it before running: export AI_API_KEY=sk-...")
        sys.exit(1)

    reset_ai_provider()
    provider = create_ai_provider(settings)
    model_info = provider.get_model_info()

    print(f"\n{'='*60}")
    print(f"TaskMate AI Evaluation")
    print(f"{'='*60}")
    print(f"Provider: {model_info.provider}")
    print(f"Model: {model_info.model}")
    print(f"Dataset: {len(dataset)} test cases")
    print(f"{'='*60}\n")

    results = []
    intent_correct = 0
    total_entity_checks = 0
    entity_correct = 0
    total_tokens = 0
    total_latency = 0
    errors = 0

    for i, test_case in enumerate(dataset, 1):
        print(f"  [{i}/{len(dataset)}] {test_case['message'][:60]}...", end=" ")

        result = await evaluate_single(
            provider, test_case["message"], test_case["expected_intent"]
        )

        if not result["success"]:
            print(f"ERROR: {result.get('error', 'unknown')}")
            errors += 1
            results.append({**test_case, "result": result})
            continue

        # Check intent
        if result["intent_correct"]:
            intent_correct += 1
            print("\u2713", end=" ")
        else:
            print(f"\u2717 (got {result['detected_intent']})", end=" ")

        # Check entities
        entity_results = check_entity_match(
            test_case.get("expected_entities", {}),
            result.get("entities", {}),
        )
        for key, matched in entity_results.items():
            total_entity_checks += 1
            if matched:
                entity_correct += 1

        total_tokens += result.get("tokens", 0)
        total_latency += result.get("latency_ms", 0)

        result["entity_results"] = entity_results
        results.append({**test_case, "result": result})
        print(f"({result['latency_ms']}ms)")

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    # Calculate metrics
    successful = len(dataset) - errors
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": model_info.provider,
        "model": model_info.model,
        "total_cases": len(dataset),
        "successful_cases": successful,
        "errors": errors,
        "intent_accuracy": round(intent_correct / successful, 4) if successful > 0 else 0,
        "entity_accuracy": round(entity_correct / total_entity_checks, 4) if total_entity_checks > 0 else 0,
        "total_tokens": total_tokens,
        "avg_latency_ms": round(total_latency / successful) if successful > 0 else 0,
        "error_rate": round(errors / len(dataset), 4),
        "prompt_versions": {
            "system": SYSTEM_PROMPT.versioned_name,
        },
    }

    # Print report
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"  Intent Accuracy:  {metrics['intent_accuracy']*100:.1f}% ({intent_correct}/{successful})")
    print(f"  Entity Accuracy:  {metrics['entity_accuracy']*100:.1f}% ({entity_correct}/{total_entity_checks})")
    print(f"  Error Rate:       {metrics['error_rate']*100:.1f}% ({errors}/{len(dataset)})")
    print(f"  Avg Latency:      {metrics['avg_latency_ms']}ms")
    print(f"  Total Tokens:     {total_tokens}")
    print(f"{'='*60}\n")

    # Save results
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"eval_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump({"metrics": metrics, "results": results}, f, indent=2, default=str)
    print(f"Results saved to: {output_file}")

    return metrics


if __name__ == "__main__":
    asyncio.run(run_evaluation())
