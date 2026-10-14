"""Route-level tests for POST /api/v1/agent/run against the real orchestrator and database.

Only the LLM is scripted; conversation, execution and tool services are the production ones.
"""

import uuid

import pytest
from sqlalchemy import select

from app.ai.providers.base import AIResponse, BaseAIProvider, ModelInfo, ToolCallRequest
from app.models.agent_execution import AgentExecution, AgentExecutionStep
from app.models.ai import ConversationMessage


class ScriptedProvider(BaseAIProvider):
    """Returns pre-defined responses in order, recording what it was sent."""

    def __init__(self, responses: list[AIResponse]):
        self.responses = list(responses)
        self.calls: list[list] = []

    async def generate(self, messages, **kwargs):
        self.calls.append(messages)
        return self.responses.pop(0)

    async def health_check(self) -> bool:
        return True

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="scripted", model="scripted-test", max_tokens=1024, supports_tool_calling=True)


@pytest.fixture
def use_provider(monkeypatch):
    def _use(provider: BaseAIProvider):
        monkeypatch.setattr("app.api.deps.get_ai_provider", lambda: provider)
        return provider

    return _use


async def test_agent_run_plain_answer_persists_execution_and_messages(auth_client, db_session, use_provider):
    provider = use_provider(ScriptedProvider([AIResponse(content="You have no overdue tasks.")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "What is overdue?"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["message"] == "You have no overdue tasks."
    # Workspace context reached the model in the system prompt.
    assert "Workspace Context" in provider.calls[0][0].content

    execution = await db_session.get(AgentExecution, body["execution_id"])
    assert execution is not None and execution.status == "COMPLETED"
    assert str(execution.user_id) == str(auth_client._test_user.id)

    messages = (
        (
            await db_session.execute(
                select(ConversationMessage).where(ConversationMessage.conversation_id == body["conversation_id"])
            )
        )
        .scalars()
        .all()
    )
    assert [m.role for m in messages] == ["user", "assistant"]


async def test_agent_run_executes_read_tool(auth_client, db_session, use_provider, create_test_task):
    await create_test_task(auth_client._test_user.id, title="Fix login bug")
    use_provider(
        ScriptedProvider(
            [
                AIResponse(
                    content="", tool_calls=[ToolCallRequest(id="c1", name="task.search", arguments={"query": "login"})]
                ),
                AIResponse(content="Found 1 task: Fix login bug."),
            ]
        )
    )

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "Find my login tasks"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"
    steps = (
        (
            await db_session.execute(
                select(AgentExecutionStep).where(AgentExecutionStep.execution_id == resp.json()["execution_id"])
            )
        )
        .scalars()
        .all()
    )
    assert [s.tool_name for s in steps] == ["task.search"]


async def test_agent_write_tool_waits_for_approval_and_does_not_write(auth_client, db_session, use_provider):
    use_provider(
        ScriptedProvider(
            [
                AIResponse(
                    content="",
                    tool_calls=[ToolCallRequest(id="c1", name="task.create", arguments={"title": "Agent task"})],
                )
            ]
        )
    )

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "Create a task called Agent task"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "WAITING_FOR_APPROVAL"
    tasks = await auth_client.get("/api/v1/tasks/", params={"search": "Agent task"})
    assert tasks.json()["total"] == 0


async def test_agent_ignores_conversation_of_another_user(client, create_test_user, db_session, use_provider):
    use_provider(ScriptedProvider([AIResponse(content="first"), AIResponse(content="second")]))
    _, token_a = await create_test_user(email="a@example.com")
    _, token_b = await create_test_user(email="b@example.com")

    first = await client.post(
        "/api/v1/agent/run", json={"prompt": "hi"}, headers={"Authorization": f"Bearer {token_a}"}
    )
    conv_a = first.json()["conversation_id"]

    second = await client.post(
        "/api/v1/agent/run",
        json={"prompt": "hi", "conversation_id": conv_a},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] != conv_a


async def test_agent_run_requires_auth(client):
    resp = await client.post("/api/v1/agent/run", json={"prompt": "hi", "conversation_id": str(uuid.uuid4())})
    assert resp.status_code == 401


def _search_call(i: int) -> AIResponse:
    return AIResponse(content="", tool_calls=[ToolCallRequest(id=f"c{i}", name="task.search", arguments={})])


async def test_agent_answer_on_last_allowed_step_is_completed_not_timeout(auth_client, use_provider, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "AGENT_MAX_STEPS", 2)
    use_provider(ScriptedProvider([_search_call(1), AIResponse(content="done")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})

    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["message"] == "done"


async def test_agent_step_limit_marks_timeout(auth_client, use_provider, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "AGENT_MAX_STEPS", 2)
    use_provider(ScriptedProvider([_search_call(1), _search_call(2)]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})

    assert resp.json()["status"] == "TIMEOUT"
    assert "step limit" in resp.json()["message"]


async def test_agent_tool_exception_fails_step_not_run(auth_client, db_session, use_provider, monkeypatch):
    from app.agent.tools.task_tools import TaskSearchTool

    async def boom(self, input_data, context):
        raise RuntimeError("database exploded")

    monkeypatch.setattr(TaskSearchTool, "execute", boom)
    use_provider(ScriptedProvider([_search_call(1), AIResponse(content="Sorry, search failed.")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})

    assert resp.json()["status"] == "COMPLETED"
    step = (
        await db_session.execute(
            select(AgentExecutionStep).where(AgentExecutionStep.execution_id == resp.json()["execution_id"])
        )
    ).scalar_one()
    assert step.status == "FAILED" and "database exploded" in step.error


@pytest.mark.parametrize("project_id", ["not-a-uuid", str(uuid.uuid4())])
async def test_agent_task_create_with_bad_project_is_denied(auth_client, db_session, use_provider, project_id):
    use_provider(
        ScriptedProvider(
            [
                AIResponse(
                    content="",
                    tool_calls=[
                        ToolCallRequest(id="c1", name="task.create", arguments={"title": "x", "project_id": project_id})
                    ],
                ),
                AIResponse(content="I couldn't access that project."),
            ]
        )
    )

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})

    assert resp.json()["status"] == "COMPLETED"
    step = (
        await db_session.execute(
            select(AgentExecutionStep).where(AgentExecutionStep.execution_id == resp.json()["execution_id"])
        )
    ).scalar_one()
    assert step.status == "FAILED" and "Permission denied" in step.error


async def test_agent_task_create_in_own_project_reaches_approval(auth_client, use_provider, create_test_project):
    project = await create_test_project(auth_client._test_user.id)
    use_provider(
        ScriptedProvider(
            [
                AIResponse(
                    content="",
                    tool_calls=[
                        ToolCallRequest(id="c1", name="task.create", arguments={"title": "x", "project_id": project.id})
                    ],
                )
            ]
        )
    )

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})

    assert resp.json()["status"] == "WAITING_FOR_APPROVAL"


async def test_agent_run_with_real_configured_provider(auth_client):
    """No monkeypatching: exercises the provider the app actually builds (mock in tests)."""
    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "What should I work on today?"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["message"]
