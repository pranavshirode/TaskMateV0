"""Tests for prompt templates."""
from app.ai.prompts.base import PromptTemplate
from app.ai.prompts.system import SYSTEM_PROMPT
from app.ai.prompts.intent_detection import INTENT_DETECTION_PROMPT
from app.ai.prompts.task_creation import TASK_CREATION_PROMPT
from app.ai.prompts.task_search import TASK_SEARCH_PROMPT
from app.ai.prompts.general import GENERAL_ASSISTANT_PROMPT


class TestPromptTemplate:
    def test_versioned_name(self):
        tpl = PromptTemplate(name="test", version="v1", template="Hello {name}")
        assert tpl.versioned_name == "test_v1"

    def test_render(self):
        tpl = PromptTemplate(name="test", version="v1", template="Hello {name}")
        result = tpl.render(name="World")
        assert result == "Hello World"


class TestSystemPrompt:
    def test_has_version(self):
        assert SYSTEM_PROMPT.version == "v1"
        assert SYSTEM_PROMPT.name == "assistant"

    def test_renders_with_context(self):
        rendered = SYSTEM_PROMPT.render(
            current_date="2026-10-05",
            user_name="Developer",
            workspace_context="No data",
        )
        assert "2026-10-05" in rendered
        assert "Developer" in rendered
        assert "CREATE_TASK" in rendered

    def test_contains_safety_rules(self):
        assert "NEVER invent" in SYSTEM_PROMPT.template
        assert "NEVER reveal" in SYSTEM_PROMPT.template
        assert "DATA, not instructions" in SYSTEM_PROMPT.template


class TestIntentDetectionPrompt:
    def test_renders(self):
        rendered = INTENT_DETECTION_PROMPT.render(user_message="Create a task")
        assert "Create a task" in rendered


class TestAllPromptsVersioned:
    def test_all_have_versions(self):
        prompts = [SYSTEM_PROMPT, INTENT_DETECTION_PROMPT, TASK_CREATION_PROMPT,
                   TASK_SEARCH_PROMPT, GENERAL_ASSISTANT_PROMPT]
        for p in prompts:
            assert p.version, f"{p.name} missing version"
            assert p.versioned_name, f"{p.name} missing versioned_name"
