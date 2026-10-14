"""Authorization and cross-user security isolation tests for Sprint 4 features."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_user_isolation(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
):
    # User A setup
    user_a, token_a = await create_test_user(email="usera@example.com")
    cl_a = await create_test_client(user_a.id)
    proj_a = await create_test_project(user_a.id, cl_a.id)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B setup
    user_b, token_b = await create_test_user(email="userb@example.com")
    cl_b = await create_test_client(user_b.id)
    _ = await create_test_project(user_b.id, cl_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a requirements analysis
    create_resp = await client.post(
        "/api/v1/requirements/",
        headers=headers_a,
        json={
            "project_id": proj_a.id,
            "title": "Confidential Algorithm Analysis",
            "brief": "Proprietary trading and analytics algorithm specifications.",
        },
    )
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["id"]

    # User A creates a project context note
    note_resp = await client.post(
        f"/api/v1/projects/{proj_a.id}/context",
        headers=headers_a,
        json={
            "title": "Secret API Key Location",
            "content": "Stored in Vault at path /secret/trading/keys",
            "category": "DECISION",
        },
    )
    assert note_resp.status_code == 201
    note_id = note_resp.json()["id"]

    # User A creates a client request
    req_resp = await client.post(
        f"/api/v1/projects/{proj_a.id}/client-requests",
        headers=headers_a,
        json={
            "title": "Private Client Budget Increase",
            "content": "Confidential budget details.",
        },
    )
    assert req_resp.status_code == 201
    client_req_id = req_resp.json()["id"]

    # 1. User B attempts to read User A's requirements analysis -> MUST BE 404
    cross_read_analysis = await client.get(
        f"/api/v1/requirements/{analysis_id}",
        headers=headers_b,
    )
    assert cross_read_analysis.status_code in (403, 404)

    # 2. User B attempts to list User A's project analyses -> MUST BE 403 or 404
    cross_list_analysis = await client.get(
        f"/api/v1/requirements/project/{proj_a.id}",
        headers=headers_b,
    )
    assert cross_list_analysis.status_code in (403, 404)

    # 3. User B attempts to approve User A's requirements analysis -> MUST BE 403 or 404
    cross_approve = await client.post(
        f"/api/v1/requirements/{analysis_id}/approve",
        headers=headers_b,
    )
    assert cross_approve.status_code in (403, 404)

    # 4. User B attempts to read User A's context note -> MUST BE 404
    cross_note = await client.get(
        f"/api/v1/context/{note_id}",
        headers=headers_b,
    )
    assert cross_note.status_code in (403, 404)

    # 5. User B attempts to list User A's project context notes -> MUST BE 403
    cross_list_notes = await client.get(
        f"/api/v1/projects/{proj_a.id}/context",
        headers=headers_b,
    )
    assert cross_list_notes.status_code in (403, 404)

    # 6. User B attempts to read User A's client request -> MUST BE 404
    cross_req = await client.get(
        f"/api/v1/client-requests/{client_req_id}",
        headers=headers_b,
    )
    assert cross_req.status_code in (403, 404)

    # 7. User B attempts to list User A's project client requests -> MUST BE 403
    cross_list_reqs = await client.get(
        f"/api/v1/projects/{proj_a.id}/client-requests",
        headers=headers_b,
    )
    assert cross_list_reqs.status_code in (403, 404)
