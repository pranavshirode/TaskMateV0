#!/usr/bin/env python3
"""TaskMate AI — Intent Classifier Training & Evaluation Pipeline.

Phase 5 Deliverable:
Trains a specialized intent classification model to route workspace-wide developer
messages to domain actions (tasks, clients, projects) and multi-step agent workflows.

Methodology:
- Dataset: evaluation/dataset.json (100 labeled real-world workspace prompts)
- Preprocessing: N-gram tokenization, sublinear TF-IDF scaling, lowercasing
- Baseline Model: Multinomial Naive Bayes with CountVectorizer
- Candidate Model: Calibrated Logistic Regression with TF-IDF (1-2 grams)
- Evaluation: Macro F1, Precision, Recall, Accuracy, Confusion Matrix on held-out split
- Output Artifacts:
  - app/ai/artifacts/intent_classifier_v1.joblib (serialized pipeline)
  - app/ai/artifacts/intent_classifier_v1_meta.json (model metadata & metrics)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def load_dataset(dataset_path: Path) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Load and validate the intent classification dataset."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts: list[str] = []
    labels: list[str] = []
    raw_records: list[dict[str, Any]] = []

    for item in data:
        msg = item.get("message", "").strip()
        intent = item.get("expected_intent", "").strip()
        if msg and intent:
            texts.append(msg)
            labels.append(intent)
            raw_records.append(item)

    return texts, labels, raw_records


def create_train_test_split(
    texts: list[str], labels: list[str], test_size: float = 0.2, random_state: int = 42
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Create reproducible train and held-out test splits.
    
    Handles rare classes with single samples by ensuring they appear in the train set.
    """
    label_counts: dict[str, int] = {}
    for l in labels:
        label_counts[l] = label_counts.get(l, 0) + 1

    # Singletons must be in train split
    singleton_indices = {i for i, l in enumerate(labels) if label_counts[l] < 2}
    stratified_indices = [i for i in range(len(labels)) if i not in singleton_indices]

    strat_texts = [texts[i] for i in stratified_indices]
    strat_labels = [labels[i] for i in stratified_indices]

    sss = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_sub_idx, test_sub_idx = next(sss.split(strat_texts, strat_labels))

    train_idx = list(singleton_indices) + [stratified_indices[i] for i in train_sub_idx]
    test_idx = [stratified_indices[i] for i in test_sub_idx]

    train_texts = [texts[i] for i in train_idx]
    train_labels = [labels[i] for i in train_idx]
    test_texts = [texts[i] for i in test_idx]
    test_labels = [labels[i] for i in test_idx]

    return train_texts, test_texts, train_labels, test_labels


def evaluate_model(
    model: Pipeline, X_test: list[str], y_test: list[str], classes: list[str]
) -> dict[str, Any]:
    """Compute performance metrics and confusion matrix on the held-out test set."""
    y_pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0
    )
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )

    clf_report = classification_report(
        y_test, y_pred, labels=classes, zero_division=0, output_dict=True
    )
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "confusion_matrix": cm,
        "classes": classes,
        "classification_report": clf_report,
    }


def main() -> None:
    print("=" * 70)
    print("TaskMate AI — Intent Classification Model Training")
    print("=" * 70)

    dataset_path = Path(__file__).parent / "dataset.json"
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        sys.exit(1)

    texts, labels, _ = load_dataset(dataset_path)
    print(f"Loaded {len(texts)} samples across {len(set(labels))} classes from {dataset_path.name}.")

    # 1. Train / Test Split
    X_train, X_test, y_train, y_test = create_train_test_split(texts, labels, test_size=0.2, random_state=42)
    print(f"Split sizes: Train={len(X_train)} samples, Held-out Test={len(X_test)} samples.")

    unique_classes = sorted(list(set(labels)))

    # 2. Train Baseline (Multinomial Naive Bayes)
    baseline_pipeline = Pipeline([
        ("vect", CountVectorizer(lowercase=True, stop_words="english")),
        ("clf", MultinomialNB(alpha=1.0)),
    ])
    baseline_pipeline.fit(X_train, y_train)
    baseline_metrics = evaluate_model(baseline_pipeline, X_test, y_test, unique_classes)
    print("\n--- Baseline Model (CountVectorizer + MultinomialNB) ---")
    print(f"Accuracy:         {baseline_metrics['accuracy'] * 100:.2f}%")
    print(f"Macro F1 Score:   {baseline_metrics['macro_f1'] * 100:.2f}%")
    print(f"Macro Precision:  {baseline_metrics['macro_precision'] * 100:.2f}%")
    print(f"Macro Recall:     {baseline_metrics['macro_recall'] * 100:.2f}%")

    # 3. Train Primary Model (TF-IDF + Calibrated Logistic Regression)
    primary_pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                lowercase=True,
                min_df=1,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                C=3.0,
                penalty="l2",
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            ),
        ),
    ])
    primary_pipeline.fit(X_train, y_train)
    primary_metrics = evaluate_model(primary_pipeline, X_test, y_test, unique_classes)

    print("\n--- Primary Model (TF-IDF [1,2] + Balanced Logistic Regression) ---")
    print(f"Accuracy:         {primary_metrics['accuracy'] * 100:.2f}%")
    print(f"Macro F1 Score:   {primary_metrics['macro_f1'] * 100:.2f}%")
    print(f"Macro Precision:  {primary_metrics['macro_precision'] * 100:.2f}%")
    print(f"Macro Recall:     {primary_metrics['macro_recall'] * 100:.2f}%")

    # 4. Save Artifacts
    artifacts_dir = Path(__file__).parent.parent / "app" / "ai" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    model_artifact_path = artifacts_dir / "intent_classifier_v1.joblib"
    meta_path = artifacts_dir / "intent_classifier_v1_meta.json"

    joblib.dump(primary_pipeline, model_artifact_path)
    print(f"\nModel artifact serialized to: {model_artifact_path}")

    meta = {
        "model_name": "TaskMate Workspace Intent Classifier",
        "model_version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TF-IDF (1,2 ngrams) + LogisticRegression(C=3.0, class_weight='balanced')",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "total_samples": len(texts),
        "classes": unique_classes,
        "baseline_metrics": {
            "model": "CountVectorizer + MultinomialNB",
            "accuracy": baseline_metrics["accuracy"],
            "macro_f1": baseline_metrics["macro_f1"],
            "macro_precision": baseline_metrics["macro_precision"],
            "macro_recall": baseline_metrics["macro_recall"],
        },
        "primary_metrics": {
            "model": "TfidfVectorizer + LogisticRegression",
            "accuracy": primary_metrics["accuracy"],
            "macro_f1": primary_metrics["macro_f1"],
            "macro_precision": primary_metrics["macro_precision"],
            "macro_recall": primary_metrics["macro_recall"],
            "weighted_f1": primary_metrics["weighted_f1"],
        },
        "classification_report": primary_metrics["classification_report"],
        "confusion_matrix": primary_metrics["confusion_matrix"],
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata and evaluation report saved to: {meta_path}")

    # 5. Sanity Check Inference
    test_queries = [
        "Create a high priority task to update the Stripe webhook",
        "Check my open GitHub pull requests and summarize failing tests",
        "Show all tasks due today for Acme Corp",
        "What is the status of the Mobile App project?",
        "Can you explain what an API key is?",
    ]
    print("\n--- Verification Inference Examples ---")
    for q in test_queries:
        probs = primary_pipeline.predict_proba([q])[0]
        pred_idx = np.argmax(probs)
        pred_label = primary_pipeline.classes_[pred_idx]
        confidence = float(probs[pred_idx])
        print(f"Query: \"{q}\"")
        print(f"  → Predicted Intent: {pred_label} (Confidence: {confidence:.2%})\n")

    print("Training and evaluation completed successfully!")


if __name__ == "__main__":
    main()

