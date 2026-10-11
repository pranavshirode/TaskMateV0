"""Automated test execution of the 32-scenario Requirements AI evaluation suite."""
import pytest
from evaluation.evaluate_requirements import run_all_evaluations


@pytest.mark.asyncio
async def test_requirements_evaluation_suite():
    results = await run_all_evaluations()
    assert results["total"] >= 30, f"Expected at least 30 scenarios, got {results['total']}"
    assert results["failed"] == 0, f"Evaluation failures: {[r for r in results['results'] if not r['success']]}"
    assert results["accuracy_percent"] == 100.0

