"""Agent write approval flow (audit BUG-02): approve runs once, reject never runs, owners only."""

import pytest

from app.ai.providers.base import AIResponse, ToolCallRequest
from tests.test_agent.test_agent_route import ScriptedProvider


def _create_task_call(title="Write onboarding email"):
    return AIResponse(
        content="",
        tool_calls=[ToolCallRequest(id="c1", name="task.create", arguments={"title": title, "priority": "HIGH"})],
    )


@pytest.fixture
def waiting_run(auth_client, monkeypatch):
    async def _run(title="Write onboarding email"):
        monkeypatch.setattr("app.api.deps.get_ai_provider", lambda: ScriptedProvider([_create_task_call(title)]))
        resp = await auth_client.post("/api/v1/agent/run", json={"prompt": f"Create a task {title}"})
        assert resp.json()["status"] == "WAITING_FOR_APPROVAL"
        return resp.json()

    return _run


async def _task_count(client, title):
    return (await client.get("/api/v1/tasks/", params={"search": title})).json()["total"]


async def test_run_returns_reviewable_pending_action(auth_client, waiting_run):
    body = await waiting_run()

    action = body["pending_action"]
    assert action["tool_name"] == "task.create"
    assert action["arguments"]["title"] == "Write onboarding email"
    assert "Write onboarding email" in action["summary"]
    assert await _task_count(auth_client, "Write onboarding email") == 0


async def test_approve_executes_exactly_once(auth_client, waiting_run):
    body = await waiting_run()
    url = f"/api/v1/agent/executions/{body['execution_id']}/approve"

    first = await auth_client.post(url)
    second = await auth_client.post(url)

    assert first.status_code == 200 and first.json()["status"] == "COMPLETED"
    assert first.json()["message"].startswith("Done:")
    assert second.status_code == 409 and second.json()["error"]["code"] == "NOT_PENDING"
    assert await _task_count(auth_client, "Write onboarding email") == 1

    trace = (await auth_client.get(f"/api/v1/agent/executions/{body['execution_id']}")).json()
    assert trace["status"] == "COMPLETED"
    assert [s["status"] for s in trace["steps"]] == ["COMPLETED"]


async def test_reject_never_writes(auth_client, waiting_run):
    body = await waiting_run()

    resp = await auth_client.post(f"/api/v1/agent/executions/{body['execution_id']}/reject")

    assert resp.status_code == 200 and resp.json()["status"] == "CANCELLED"
    assert await _task_count(auth_client, "Write onboarding email") == 0
    again = await auth_client.post(f"/api/v1/agent/executions/{body['execution_id']}/approve")
    assert again.status_code == 409


async def test_other_user_cannot_see_or_approve(auth_client, waiting_run, client, create_test_user):
    body = await waiting_run()
    owner_header = auth_client.headers["Authorization"]
    _, other_token = await create_test_user(email="intruder@example.com")
    other = {"Authorization": f"Bearer {other_token}"}

    assert (await client.get(f"/api/v1/agent/executions/{body['execution_id']}", headers=other)).status_code == 404
    resp = await client.post(f"/api/v1/agent/executions/{body['execution_id']}/approve", headers=other)
    assert resp.status_code == 404

    client.headers["Authorization"] = owner_header
    assert await _task_count(client, "Write onboarding email") == 0


async def test_approval_message_is_saved_to_conversation(auth_client, waiting_run, db_session):
    from sqlalchemy import select

    from app.models.ai import ConversationMessage

    body = await waiting_run()
    await auth_client.post(f"/api/v1/agent/executions/{body['execution_id']}/approve")

    messages = (
        (
            await db_session.execute(
                select(ConversationMessage).where(ConversationMessage.conversation_id == body["conversation_id"])
            )
        )
        .scalars()
        .all()
    )
    assert [m.role for m in messages] == ["user", "assistant", "assistant"]
    assert messages[-1].content.startswith("Done:")
