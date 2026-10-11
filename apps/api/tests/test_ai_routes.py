import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat_unauthenticated(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Hello"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_flow(auth_client: AsyncClient):
    # Send natural language message
    chat_resp = await auth_client.post(
        "/api/v1/ai/chat",
        json={"message": "Create a task to build user onboarding flow"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "conversation_id" in data
    assert "message" in data
    assert data["intent"] == "CREATE_TASK"
    conv_id = data["conversation_id"]

    # List conversations
    list_resp = await auth_client.get("/api/v1/ai/conversations")
    assert list_resp.status_code == 200
    convs = list_resp.json()
    assert len(convs) >= 1
    assert convs[0]["id"] == conv_id

    # Get conversation details
    detail_resp = await auth_client.get(f"/api/v1/ai/conversations/{conv_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) >= 2  # user + assistant

    # Check usage stats
    usage_resp = await auth_client.get("/api/v1/ai/usage")
    assert usage_resp.status_code == 200
    usage = usage_resp.json()
    assert usage["total_requests"] >= 1

    # Delete conversation
    del_resp = await auth_client.delete(f"/api/v1/ai/conversations/{conv_id}")
    assert del_resp.status_code == 204

