"""End-to-end: agent -> MCP client -> real MCP server over HTTP, with per-user credentials and approvals."""

import pytest

from app.ai.providers.base import AIResponse, ToolCallRequest
from app.integrations.mcp.client import MCPClientManager, MCPError
from tests.test_agent.test_agent_route import ScriptedProvider
from tests.test_mcp.conftest import VALID_TOKEN


class RecordingProvider(ScriptedProvider):
    async def generate(self, messages, **kwargs):
        self.tools_seen = [t.name for t in kwargs.get("tools") or []]
        return await super().generate(messages, **kwargs)


def call(name, **arguments):
    return AIResponse(content="", tool_calls=[ToolCallRequest(id="c1", name=name, arguments=arguments)])


@pytest.fixture
def use_provider(monkeypatch):
    def _use(provider):
        monkeypatch.setattr("app.api.deps.get_ai_provider", lambda: provider)
        return provider

    return _use


async def test_client_lists_tools_and_rejects_bad_credentials(fake_workspace, mcp_settings):
    manager = MCPClientManager(timeout=10)

    tools = await manager.list_tools(fake_workspace.url, {"Authorization": f"Bearer {VALID_TOKEN}"})
    assert {t.name for t in tools} >= {"search_gmail_messages", "send_gmail_message"}

    with pytest.raises(MCPError, match="rejected the account's credentials"):
        await manager.list_tools(fake_workspace.url, {"Authorization": "Bearer stolen"})
    with pytest.raises(MCPError, match="unreachable"):
        await manager.list_tools("http://127.0.0.1:9/mcp", {})


async def test_connected_user_gets_tools_with_hidden_account_argument(auth_client, connect_google, use_provider):
    await connect_google(auth_client._test_user)
    provider = use_provider(RecordingProvider([AIResponse(content="ok")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "hi"})

    assert resp.status_code == 200
    assert "mcp.google.search_gmail_messages" in provider.tools_seen
    status = (await auth_client.get("/api/v1/integrations/mcp")).json()
    google = next(s for s in status if s["key"] == "google")
    assert google["connected"] and google["account"] == "alex@gmail.com" and not google["error"]
    perms = {t["name"]: t["permission"] for t in google["tools"]}
    assert perms["mcp.google.search_gmail_messages"] == "READ"
    assert perms["mcp.google.send_gmail_message"] == "WRITE"
    assert perms["mcp.google.unannotated_tool"] == "WRITE"  # no annotation => not trusted as read-only
    # The model is told about the connection, and never sees the account argument.
    system_prompt = provider.calls[0][0].content
    assert "Google Workspace: connected as alex@gmail.com" in system_prompt


async def test_read_tool_runs_directly_with_injected_account(auth_client, connect_google, use_provider, fake_workspace):
    await connect_google(auth_client._test_user)
    # The model tries to target someone else's mailbox; TaskMate must override it.
    use_provider(
        ScriptedProvider(
            [
                call("mcp.google.search_gmail_messages", query="invoice", user_google_email="victim@gmail.com"),
                AIResponse(content="Found 2 emails."),
            ]
        )
    )

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "find invoice emails"})

    assert resp.json()["status"] == "COMPLETED"
    assert fake_workspace.calls == [
        ("search_gmail_messages", {"query": "invoice", "user_google_email": "alex@gmail.com"})
    ]
    assert set(fake_workspace.auth_headers) == {f"Bearer {VALID_TOKEN}"}


async def test_external_content_is_marked_untrusted(auth_client, connect_google, use_provider):
    await connect_google(auth_client._test_user)
    provider = use_provider(
        ScriptedProvider([call("mcp.google.search_gmail_messages", query="x"), AIResponse(content="done")])
    )

    await auth_client.post("/api/v1/agent/run", json={"prompt": "search"})

    tool_message = next(m for m in provider.calls[1] if getattr(m.role, "value", m.role) == "tool")
    assert "untrusted" in tool_message.content and "IGNORE PREVIOUS INSTRUCTIONS" in tool_message.content


@pytest.mark.parametrize("approval_setting", [True, False])
async def test_sending_email_always_needs_approval_and_runs_once(
    auth_client, connect_google, use_provider, fake_workspace, monkeypatch, mcp_settings, approval_setting
):
    monkeypatch.setattr(mcp_settings, "AGENT_REQUIRE_APPROVAL_FOR_WRITES", approval_setting)
    await connect_google(auth_client._test_user)
    use_provider(
        ScriptedProvider([call("mcp.google.send_gmail_message", to="client@acme.com", subject="Update", body="Hi")])
    )

    run = (await auth_client.post("/api/v1/agent/run", json={"prompt": "email the client"})).json()

    assert run["status"] == "WAITING_FOR_APPROVAL"
    assert run["pending_action"]["summary"].startswith("Google: send gmail message")
    assert "client@acme.com" in run["pending_action"]["summary"]
    assert fake_workspace.calls == []  # nothing sent before approval

    url = f"/api/v1/agent/executions/{run['execution_id']}/approve"
    first, second = await auth_client.post(url), await auth_client.post(url)

    assert first.status_code == 200 and first.json()["status"] == "COMPLETED"
    assert second.status_code == 409
    assert [c[0] for c in fake_workspace.calls] == ["send_gmail_message"]
    assert fake_workspace.calls[0][1]["user_google_email"] == "alex@gmail.com"


async def test_rejecting_email_sends_nothing(auth_client, connect_google, use_provider, fake_workspace):
    await connect_google(auth_client._test_user)
    use_provider(ScriptedProvider([call("mcp.google.send_gmail_message", to="a@b.com", subject="s", body="b")]))

    run = (await auth_client.post("/api/v1/agent/run", json={"prompt": "email"})).json()
    await auth_client.post(f"/api/v1/agent/executions/{run['execution_id']}/reject")

    assert fake_workspace.calls == []


async def test_tool_error_is_reported_not_crashing(auth_client, connect_google, use_provider):
    await connect_google(auth_client._test_user)
    use_provider(ScriptedProvider([call("mcp.google.failing_tool"), AIResponse(content="It failed.")]))

    resp = (await auth_client.post("/api/v1/agent/run", json={"prompt": "x"})).json()

    assert resp["status"] == "COMPLETED"
    trace = (await auth_client.get(f"/api/v1/agent/executions/{resp['execution_id']}")).json()
    assert trace["steps"][0]["status"] == "FAILED" and "Drive quota exceeded" in trace["steps"][0]["error"]


async def test_user_without_connection_gets_no_external_tools(auth_client, use_provider, mcp_settings, fake_workspace):
    provider = use_provider(RecordingProvider([AIResponse(content="ok")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "hi"})

    assert resp.status_code == 200
    assert not [t for t in provider.tools_seen if t.startswith("mcp.")]
    assert fake_workspace.auth_headers == []  # never contacted on behalf of an unconnected user
    assert "Google Workspace: not connected" in provider.calls[0][0].content


async def test_unreachable_server_does_not_break_the_agent(
    auth_client, connect_google, use_provider, monkeypatch, mcp_settings
):
    monkeypatch.setattr(mcp_settings, "MCP_GOOGLE_URL", "http://127.0.0.1:9/mcp")
    await connect_google(auth_client._test_user)
    provider = use_provider(RecordingProvider([AIResponse(content="Your tasks are fine.")]))

    resp = await auth_client.post("/api/v1/agent/run", json={"prompt": "status?"})

    assert resp.json()["status"] == "COMPLETED"
    assert "unavailable: the server is unreachable" in provider.calls[0][0].content


async def test_each_user_uses_their_own_google_account(
    client, create_test_user, connect_google, use_provider, fake_workspace, monkeypatch
):
    user_a, token_a = await create_test_user(email="a@example.com")
    user_b, token_b = await create_test_user(email="b@example.com")
    await connect_google(user_a, email="a@gmail.com")
    await connect_google(user_b, email="b@gmail.com")

    for token in (token_a, token_b):
        use_provider(ScriptedProvider([call("mcp.google.search_gmail_messages", query="q"), AIResponse(content="ok")]))
        await client.post("/api/v1/agent/run", json={"prompt": "s"}, headers={"Authorization": f"Bearer {token}"})

    assert [c[1]["user_google_email"] for c in fake_workspace.calls] == ["a@gmail.com", "b@gmail.com"]
