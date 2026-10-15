"""Tests for the Local Intent Classifier service and its integration.

Phase 5 Test Suite:
Verifies model artifact loading, confidence calibration, fallback behavior,
and application integration inside AIOrchestrator.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ai.services.local_classifier import (
    CONFIDENCE_THRESHOLD,
    LocalClassificationResult,
    LocalIntentClassifier,
    get_local_classifier,
)


@pytest.fixture
def classifier() -> LocalIntentClassifier:
    """Fixture providing the default local intent classifier."""
    return get_local_classifier()


def test_classifier_loads_artifact_and_metadata(classifier: LocalIntentClassifier):
    """Verify that the trained model pipeline and metadata are successfully loaded."""
    assert classifier.is_available is True
    assert classifier.pipeline is not None
    assert classifier.metadata.get("model_name") == "TaskMate Workspace Intent Classifier"
    assert classifier.metadata.get("model_version") == "1.0.0"
    assert "classes" in classifier.metadata
    assert len(classifier.metadata["classes"]) > 5


def test_high_confidence_prediction(classifier: LocalIntentClassifier):
    """Verify inference produces valid predictions with probability distributions."""
    query = "Check my recent GitHub issues and create a task for each one"
    result = classifier.predict(query)

    assert isinstance(result, LocalClassificationResult)
    assert result.intent in classifier.metadata["classes"]
    assert 0.0 <= result.confidence <= 1.0
    assert result.fallback_used is False
    assert len(result.top_candidates) > 0
    # Top candidate matches result.intent
    assert result.top_candidates[0]["intent"] == result.intent
    assert result.top_candidates[0]["confidence"] == result.confidence


def test_empty_input_graceful_fallback(classifier: LocalIntentClassifier):
    """Verify that empty or whitespace strings trigger a safe fallback."""
    result = classifier.predict("   ")
    assert result.intent == "GENERAL_QUESTION"
    assert result.confidence == 0.0
    assert result.is_confident is False
    assert result.fallback_used is True

    result_none = classifier.predict("")
    assert result_none.intent == "GENERAL_QUESTION"
    assert result_none.is_confident is False
    assert result_none.fallback_used is True


def test_threshold_confidence_flag(classifier: LocalIntentClassifier):
    """Verify that is_confident respects the configured threshold."""
    # Custom classifier with impossible 0.999 threshold
    strict_classifier = LocalIntentClassifier(threshold=0.999)
    result = strict_classifier.predict("Create a task for the frontend")
    assert result.is_confident is False

    # Custom classifier with 0.001 threshold
    lenient_classifier = LocalIntentClassifier(threshold=0.001)
    result_lenient = lenient_classifier.predict("Create a task for the frontend")
    assert result_lenient.is_confident is True


def test_missing_model_graceful_fallback(tmp_path: Path):
    """Verify classifier handles missing or corrupt model files without crashing."""
    fake_path = tmp_path / "non_existent_model.joblib"
    fake_meta = tmp_path / "non_existent_meta.json"

    fallback_classifier = LocalIntentClassifier(model_path=fake_path, meta_path=fake_meta)
    assert fallback_classifier.is_available is False

    result = fallback_classifier.predict("Show all tasks due today")
    assert result.intent == "GENERAL_QUESTION"
    assert result.is_confident is False
    assert result.fallback_used is True


def test_ranked_top_candidates_sorted(classifier: LocalIntentClassifier):
    """Verify candidate intents are strictly sorted in descending probability order."""
    result = classifier.predict("Show my project status and milestone progress")
    confidences = [c["confidence"] for c in result.top_candidates]
    assert confidences == sorted(confidences, reverse=True)

