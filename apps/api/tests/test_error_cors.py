"""Unhandled errors must still carry CORS headers so the browser can show them (audit BUG-09)."""

import pytest
from httpx import ASGITransport, AsyncClient

ORIGIN = "http://localhost:3000"


@pytest.fixture
async def boom_client(app):
    async def boom():
        raise RuntimeError("secret internal detail")

    app.add_api_route("/boom", boom)
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as c:
        yield c


async def test_unhandled_error_has_cors_headers_and_generic_body(boom_client):
    resp = await boom_client.get("/boom", headers={"Origin": ORIGIN})

    assert resp.status_code == 500
    assert resp.headers.get("access-control-allow-origin") == ORIGIN
    assert resp.headers.get("x-request-id")
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "secret internal detail" not in resp.text
