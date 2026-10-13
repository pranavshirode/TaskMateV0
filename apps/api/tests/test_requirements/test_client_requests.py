"""Integration tests for Client Requests and Change Impact Analysis."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_client_request_lifecycle_and_impact(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
):
    user, token = await create_test_user(email="request_user@example.com")
    cl = await create_test_client(user.id)
    proj = await create_test_project(user.id, cl.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Record incoming client request
    create_resp = await client.post(
        f"/api/v1/projects/{proj.id}/client-requests",
        headers=headers,
        json={
            "title": "Add Apple Pay support",
            "content": "Client emailed: Could we also enable Apple Pay on the checkout page before next month's launch?",
            "request_type": "CHANGE_REQUEST",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    req_data = create_resp.json()
    req_id = req_data["id"]
    assert req_data["status"] == "SUBMITTED"
    assert req_data["request_type"] == "CHANGE_REQUEST"

    # 2. List client requests
    list_resp = await client.get(
        f"/api/v1/projects/{proj.id}/client-requests",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Analyze impact of request
    impact_resp = await client.post(
        f"/api/v1/client-requests/{req_id}/analyze-impact",
        headers=headers,
    )
    assert impact_resp.status_code == 200, impact_resp.text
    impact = impact_resp.json()
    assert impact["request_type"] == "CHANGE_REQUEST"
    assert "scope_change_summary" in impact
    assert len(impact["recommended_actions"]) >= 1

    # 4. Verify request status transitioned to IMPACT_REVIEWED
    get_resp = await client.get(
        f"/api/v1/client-requests/{req_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "IMPACT_REVIEWED"

    # 5. Approve client request
    approve_resp = await client.post(
        f"/api/v1/client-requests/{req_id}/approve",
        headers=headers,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
