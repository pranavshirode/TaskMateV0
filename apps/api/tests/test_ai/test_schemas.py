"""Tests for AI schemas."""
import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.ai.schemas.intent import IntentType, IntentResult, ExtractedEntities, MUTATING_INTENTS, READ_ONLY_INTENTS
from app.ai.schemas.actions import (
    CreateTaskAction, ChangeTaskStatusAction, ChangeTaskPriorityAction,
    SearchTasksAction, CompleteTaskAction, GetTodayTasksAction,
)
from app.ai.schemas.responses import AIChatRequest, AIChatResponse, AIActionResult, ContextSummary


class TestIntentType:
    def test_all_intents_defined(self):
        assert len(IntentType) == 11

    def test_mutating_intents(self):
        assert IntentType.CREATE_TASK in MUTATING_INTENTS
        assert IntentType.GENERAL_QUESTION not in MUTATING_INTENTS

    def test_read_only_intents(self):
        assert IntentType.SEARCH_TASKS in READ_ONLY_INTENTS
        assert IntentType.CREATE_TASK not in READ_ONLY_INTENTS


class TestIntentResult:
    def test_valid_intent_result(self):
        result = IntentResult(
            intent=IntentType.CREATE_TASK,
            confidence=0.95,
            entities={"title": "Fix login bug", "priority": "HIGH"},
        )
        assert result.intent == IntentType.CREATE_TASK
        assert result.confidence == 0.95

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            IntentResult(intent=IntentType.CREATE_TASK, confidence=1.5)
        with pytest.raises(ValidationError):
            IntentResult(intent=IntentType.CREATE_TASK, confidence=-0.1)

    def test_invalid_intent_type(self):
        with pytest.raises(ValidationError):
            IntentResult(intent="INVALID_INTENT", confidence=0.5)


class TestExtractedEntities:
    def test_all_optional(self):
        entities = ExtractedEntities()
        assert entities.title is None
        assert entities.priority is None

    def test_partial_entities(self):
        entities = ExtractedEntities(title="Fix bug", priority="HIGH")
        assert entities.title == "Fix bug"
        assert entities.project_name is None


class TestCreateTaskAction:
    def test_valid_action(self):
        action = CreateTaskAction(
            title="Fix login bug",
            priority="HIGH",
            due_date=date(2026, 10, 10),
        )
        assert action.action_type == IntentType.CREATE_TASK
        assert action.source == "ai_assistant"

    def test_default_priority(self):
        action = CreateTaskAction(title="Some task")
        assert action.priority == "MEDIUM"


class TestChangeTaskStatusAction:
    def test_valid_status_change(self):
        task_id = uuid.uuid4()
        action = ChangeTaskStatusAction(task_id=task_id, new_status="IN_PROGRESS")
        assert action.task_id == task_id
        assert action.new_status == "IN_PROGRESS"


class TestAIChatRequest:
    def test_valid_request(self):
        req = AIChatRequest(message="Create a task")
        assert req.message == "Create a task"
        assert req.conversation_id is None

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            AIChatRequest(message="")

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            AIChatRequest(message="x" * 2001)


class TestAIChatResponse:
    def test_valid_response(self):
        response = AIChatResponse(
            message="Task created",
            intent=IntentType.CREATE_TASK,
            confidence=0.95,
            conversation_id=uuid.uuid4(),
        )
        assert response.requires_clarification is False
        assert response.actions == []
        assert response.suggestions == []

    def test_response_with_actions(self):
        response = AIChatResponse(
            message="Done",
            conversation_id=uuid.uuid4(),
            actions=[AIActionResult(action_type=IntentType.CREATE_TASK, success=True)],
        )
        assert len(response.actions) == 1
        assert response.actions[0].success is True
