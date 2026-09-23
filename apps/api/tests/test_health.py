from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "taskmate-api"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_ready_ok(app, client: AsyncClient, monkeypatch):
    from app.db.session import get_db

    async def mock_get_db():
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db

    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_ready_error(app, client: AsyncClient, monkeypatch):
    from app.db.session import get_db

    async def mock_get_db():
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("DB connection failed")
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db

    response = await client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert "error" in data["checks"]["database"]

    app.dependency_overrides.clear()
