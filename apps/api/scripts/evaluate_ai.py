"""AI Evaluation Script.

Evaluates intent classification accuracy, entity extraction, and latency
across the evaluation dataset.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time

# Ensure app is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.providers import get_ai_provider
from app.ai.providers.base import AIMessage


async def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "tests", "evaluation", "eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        sys.exit(1)

    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    provider = get_ai_provider()
    print("==================================================")
    print("TASKMATE AI — SPRINT 2 EVALUATION SUITE")
    print(f"Provider: {type(provider).__name__}")
    print(f"Dataset Size: {len(dataset)} prompts")
    print("==================================================\n")

    correct_intents = 0
    total = len(dataset)
    latencies = []

    print(f"{'ID':<10} | {'Expected Intent':<20} | {'Detected Intent':<20} | {'Status':<6} | {'Latency'}")
    print("-" * 75)

    for item in dataset:
        prompt_id = item["id"]
        prompt = item["prompt"]
        expected_intent = item["expected_intent"]

        messages = [
            AIMessage(
                role="system",
                content="You are TaskMate AI. Respond with valid JSON containing intent, confidence, entities.",
            ),
            AIMessage(role="user", content=prompt),
        ]

        start = time.time()
        try:
            resp = await provider.generate(messages, response_format={"type": "json_object"})
            latency = int((time.time() - start) * 1000)
            latencies.append(latency)

            # Parse
            data = json.loads(resp.content)
            detected_intent = data.get("intent", "UNKNOWN")

            if detected_intent == expected_intent:
                correct_intents += 1
                status = "PASS"
            else:
                status = "FAIL"

            print(f"{prompt_id:<10} | {expected_intent:<20} | {detected_intent:<20} | {status:<6} | {latency}ms")
        except Exception as e:
            print(f"{prompt_id:<10} | {expected_intent:<20} | ERROR: {str(e)[:15]} | FAIL   | -")

    accuracy = (correct_intents / total) * 100 if total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print("-" * 75)
    print("\nEVALUATION SUMMARY:")
    print(f"Total Cases:     {total}")
    print(f"Passed Intents:  {correct_intents}")
    print(f"Intent Accuracy: {accuracy:.2f}%")
    print(f"Avg Latency:     {avg_latency:.1f}ms")
    print("Baseline Target: >= 85.0%")
    print(f"Result:          {'SUCCEEDED' if accuracy >= 85.0 else 'FAILED'}\n")

    return accuracy >= 85.0


if __name__ == "__main__":
    success = asyncio.run(run_evaluation())
    sys.exit(0 if success else 1)
