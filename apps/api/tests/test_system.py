import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient):
    response = await client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TaskMate API"
    assert "version" in data
    assert data["environment"] == "testing"
