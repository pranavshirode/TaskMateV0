"""Per-user Google OAuth and GitHub connection flows (HTTP to Google/GitHub replaced by MockTransport)."""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import select

from app.models.google_integration import GoogleIntegration
from app.repositories.google_integration import GoogleIntegrationRepository
from app.services.github_integration import GitHubIntegrationService
from app.services.google_integration import GoogleIntegrationService


@pytest.fixture
def google_http(monkeypatch):
    """Fake Google endpoints; records every request."""
    state = {"requests": [], "refresh_ok": True}

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        body = parse_qs(request.content.decode()) if request.content else {}
        if request.url.path == "/token" and body.get("grant_type") == ["authorization_code"]:
            if body.get("code") != ["good-code"]:
                return httpx.Response(400, json={"error": "invalid_grant", "error_description": "Bad code"})
            return httpx.Response(
                200,
                json={"access_token": "access-1", "refresh_token": "refresh-1", "expires_in": 3600, "scope": "email"},
            )
        if request.url.path == "/token" and body.get("grant_type") == ["refresh_token"]:
            if not state["refresh_ok"]:
                return httpx.Response(400, json={"error": "invalid_grant"})
            return httpx.Response(200, json={"access_token": "access-2", "expires_in": 3600})
        if request.url.path == "/v1/userinfo":
            return httpx.Response(200, json={"email": "alex@gmail.com"})
        if request.url.path == "/revoke":
            return httpx.Response(200)
        return httpx.Response(404)

    monkeypatch.setattr(GoogleIntegrationService, "transport", httpx.MockTransport(handler))
    return state


async def _state_for(auth_client):
    url = (await auth_client.get("/api/v1/integrations/google/authorize")).json()["url"]
    return url, parse_qs(urlparse(url).query)


async def test_authorize_url_requests_offline_access_and_scopes(auth_client, mcp_settings):
    url, query = await _state_for(auth_client)

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert query["client_id"] == ["client-id.apps.googleusercontent.com"]
    assert query["access_type"] == ["offline"] and query["state"]
    assert "https://www.googleapis.com/auth/gmail.readonly" in query["scope"][0]


async def test_connect_stores_tokens_encrypted(auth_client, mcp_settings, google_http, db_session):
    _, query = await _state_for(auth_client)

    resp = await auth_client.post(
        "/api/v1/integrations/google/connect", json={"code": "good-code", "state": query["state"][0]}
    )

    assert resp.status_code == 200 and resp.json() == {"configured": True, "connected": True, "email": "alex@gmail.com"}
    row = (await db_session.execute(select(GoogleIntegration))).scalar_one()
    assert "refresh-1" not in row.encrypted_refresh_token and "access-1" not in (row.encrypted_access_token or "")
    status = (await auth_client.get("/api/v1/integrations/google")).json()
    assert status["connected"] and status["email"] == "alex@gmail.com"


async def test_state_from_another_user_is_rejected(client, create_test_user, mcp_settings, google_http):
    _, token_a = await create_test_user(email="a@example.com")
    _, token_b = await create_test_user(email="b@example.com")
    url = (
        await client.get("/api/v1/integrations/google/authorize", headers={"Authorization": f"Bearer {token_a}"})
    ).json()["url"]
    state = parse_qs(urlparse(url).query)["state"][0]

    resp = await client.post(
        "/api/v1/integrations/google/connect",
        json={"code": "good-code", "state": state},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert resp.status_code == 422 and "different TaskMate account" in resp.json()["error"]["message"]
    assert not google_http["requests"]  # nothing exchanged with Google


async def test_bad_code_is_reported(auth_client, mcp_settings, google_http):
    _, query = await _state_for(auth_client)

    resp = await auth_client.post(
        "/api/v1/integrations/google/connect", json={"code": "bad", "state": query["state"][0]}
    )

    assert resp.status_code == 422 and "Bad code" in resp.json()["error"]["message"]


async def test_expired_access_token_is_refreshed(auth_client, connect_google, mcp_settings, google_http, db_session):
    await connect_google(auth_client._test_user)
    row = (await db_session.execute(select(GoogleIntegration))).scalar_one()
    row.access_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    service = GoogleIntegrationService(GoogleIntegrationRepository(db_session))
    token, email = await service.get_credentials(auth_client._test_user)

    assert (token, email) == ("access-2", "alex@gmail.com")


async def test_revoked_refresh_token_asks_user_to_reconnect(
    auth_client, connect_google, mcp_settings, google_http, db_session
):
    await connect_google(auth_client._test_user)
    row = (await db_session.execute(select(GoogleIntegration))).scalar_one()
    row.access_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()
    google_http["refresh_ok"] = False

    status = (await auth_client.get("/api/v1/integrations/mcp")).json()

    google = next(s for s in status if s["key"] == "google")
    assert google["connected"] and "Reconnect Google" in google["error"]


async def test_disconnect_revokes_and_deletes(auth_client, connect_google, mcp_settings, google_http, db_session):
    await connect_google(auth_client._test_user)

    assert (await auth_client.delete("/api/v1/integrations/google")).status_code == 200

    assert any(r.url.path == "/revoke" for r in google_http["requests"])
    assert (await db_session.execute(select(GoogleIntegration))).scalar_one_or_none() is None


async def test_google_not_configured_gives_clear_error(auth_client, monkeypatch, mcp_settings):
    monkeypatch.setattr(mcp_settings, "GOOGLE_OAUTH_CLIENT_ID", "")

    resp = await auth_client.get("/api/v1/integrations/google/authorize")

    assert resp.status_code == 422 and "not configured" in resp.json()["error"]["message"]


async def test_github_oauth_code_is_exchanged_server_side(auth_client, monkeypatch, mcp_settings):
    monkeypatch.setattr(mcp_settings, "GITHUB_CLIENT_ID", "gh-id")
    monkeypatch.setattr(mcp_settings, "GITHUB_CLIENT_SECRET", "gh-secret")
    seen = {}

    def handler(request):
        seen["body"] = parse_qs(request.content.decode())
        return httpx.Response(200, json={"access_token": "gho_real_token"})

    monkeypatch.setattr(GitHubIntegrationService, "transport", httpx.MockTransport(handler))

    class FakeUser:
        id, login, avatar_url = 1, "alexdev", None

    async def fake_user(self):
        return FakeUser()

    monkeypatch.setattr("app.integrations.github.client.GitHubClient.get_authenticated_user", fake_user)

    resp = await auth_client.post("/api/v1/integrations/github/connect", json={"code": "oauth-code"})

    assert resp.status_code == 200 and resp.json()["username"] == "alexdev"
    assert seen["body"]["code"] == ["oauth-code"] and seen["body"]["client_secret"] == ["gh-secret"]


async def test_github_personal_access_token_connects(auth_client, monkeypatch, mcp_settings):
    class FakeUser:
        id, login, avatar_url = 2, "alexdev", None

    async def fake_user(self):
        return FakeUser()

    monkeypatch.setattr("app.integrations.github.client.GitHubClient.get_authenticated_user", fake_user)

    resp = await auth_client.post("/api/v1/integrations/github/connect", json={"access_token": "  github_pat_123  "})

    assert resp.status_code == 200
    assert (await auth_client.get("/api/v1/integrations/github")).json()["username"] == "alexdev"


async def test_invalid_github_token_gives_clear_message(auth_client, monkeypatch, mcp_settings):
    async def rejected(self):
        request = httpx.Request("GET", "https://api.github.com/user")
        raise httpx.HTTPStatusError("401", request=request, response=httpx.Response(401, request=request))

    monkeypatch.setattr("app.integrations.github.client.GitHubClient.get_authenticated_user", rejected)

    resp = await auth_client.post("/api/v1/integrations/github/connect", json={"access_token": "bad"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "GitHub rejected this token. Check it was copied completely and hasn't expired."
