"""Tests for client communication and follow-up endpoints and service."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_communication_success(
    auth_client: AsyncClient, create_test_client, create_test_project
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Acme Corp")
    project = await create_test_project(user_id, client_id=client.id, name="Website Redesign")

    resp = await auth_client.post(
        "/api/v1/client-communications",
        json={
            "client_id": client.id,
            "project_id": project.id,
            "subject": "Sprint 1 Deliverables Ready for Review",
            "content": "Hi Acme team, please review the latest designs attached.",
            "channel": "EMAIL",
            "communication_type": "MILESTONE_DELIVERY",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "Sprint 1 Deliverables Ready for Review"
    assert data["status"] == "DRAFT"
    assert data["client_id"] == client.id
    assert data["project_id"] == project.id
    assert data["channel"] == "EMAIL"
    assert data["approved_at"] is None
    assert data["sent_at"] is None


@pytest.mark.asyncio
async def test_create_communication_invalid_client(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v1/client-communications",
        json={
            "client_id": "nonexistent-client-id",
            "subject": "Hello",
            "content": "Test content",
        },
    )
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_list_communications(
    auth_client: AsyncClient, create_test_client
):
    user_id = auth_client._test_user.id
    client1 = await create_test_client(user_id, name="Client 1")
    client2 = await create_test_client(user_id, name="Client 2")

    # Create one for client1 and one for client2
    await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client1.id, "subject": "Msg 1", "content": "Body 1"},
    )
    await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client2.id, "subject": "Msg 2", "content": "Body 2"},
    )

    # List all
    all_resp = await auth_client.get("/api/v1/client-communications")
    assert all_resp.status_code == 200
    assert len(all_resp.json()) >= 2

    # Filter by client1
    c1_resp = await auth_client.get(f"/api/v1/clients/{client1.id}/communications")
    assert c1_resp.status_code == 200
    c1_items = c1_resp.json()
    assert len(c1_items) == 1
    assert c1_items[0]["subject"] == "Msg 1"


@pytest.mark.asyncio
async def test_get_and_update_communication(
    auth_client: AsyncClient, create_test_client
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Beta Co")

    create_resp = await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client.id, "subject": "Original Subject", "content": "Original Content"},
    )
    assert create_resp.status_code == 201
    comm_id = create_resp.json()["id"]

    # Get single
    get_resp = await auth_client.get(f"/api/v1/client-communications/{comm_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["subject"] == "Original Subject"

    # Update
    update_resp = await auth_client.patch(
        f"/api/v1/client-communications/{comm_id}",
        json={"subject": "Updated Subject", "content": "Updated Content", "notes": "Draft updated"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["subject"] == "Updated Subject"
    assert updated["content"] == "Updated Content"
    assert updated["notes"] == "Draft updated"


@pytest.mark.asyncio
async def test_approval_flow_and_send(
    auth_client: AsyncClient, create_test_client
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Gamma Corp")

    create_resp = await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client.id, "subject": "Contract Followup", "content": "Checking in on the agreement."},
    )
    comm_id = create_resp.json()["id"]

    # Step 1: Submit for approval
    submit_resp = await auth_client.post(
        f"/api/v1/client-communications/{comm_id}/status",
        json={"status": "PENDING_APPROVAL", "notes": "Ready for manager review"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "PENDING_APPROVAL"

    # Step 2: Approve
    approve_resp = await auth_client.post(f"/api/v1/client-communications/{comm_id}/approve")
    assert approve_resp.status_code == 200
    approved_data = approve_resp.json()
    assert approved_data["status"] == "APPROVED"
    assert approved_data["approved_at"] is not None

    # Step 3: Send
    send_resp = await auth_client.post(f"/api/v1/client-communications/{comm_id}/send")
    assert send_resp.status_code == 200
    sent_data = send_resp.json()
    assert sent_data["status"] == "SENT"
    assert sent_data["sent_at"] is not None


@pytest.mark.asyncio
async def test_send_without_approval_fails(
    auth_client: AsyncClient, create_test_client
):
    """Enforce security invariant: No communication may be sent directly from DRAFT."""
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Delta Ltd")

    create_resp = await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client.id, "subject": "Unapproved", "content": "Trying to bypass approval."},
    )
    comm_id = create_resp.json()["id"]

    # Trying to send directly
    send_resp = await auth_client.post(f"/api/v1/client-communications/{comm_id}/send")
    assert send_resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_cannot_edit_or_delete_sent_communication(
    auth_client: AsyncClient, create_test_client
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Epsilon Inc")

    create_resp = await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client.id, "subject": "Final Notice", "content": "Project delivered."},
    )
    comm_id = create_resp.json()["id"]

    # Move to pending -> approved -> sent
    await auth_client.post(
        f"/api/v1/client-communications/{comm_id}/status",
        json={"status": "PENDING_APPROVAL"},
    )
    await auth_client.post(f"/api/v1/client-communications/{comm_id}/approve")
    await auth_client.post(f"/api/v1/client-communications/{comm_id}/send")

    # Attempt to edit
    patch_resp = await auth_client.patch(
        f"/api/v1/client-communications/{comm_id}",
        json={"content": "Tampered content"},
    )
    assert patch_resp.status_code in (400, 422)

    # Attempt to delete
    del_resp = await auth_client.delete(f"/api/v1/client-communications/{comm_id}")
    assert del_resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_delete_draft_communication(
    auth_client: AsyncClient, create_test_client
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Zeta Corp")

    create_resp = await auth_client.post(
        "/api/v1/client-communications",
        json={"client_id": client.id, "subject": "To Be Deleted", "content": "Temporary scratchpad."},
    )
    comm_id = create_resp.json()["id"]

    del_resp = await auth_client.delete(f"/api/v1/client-communications/{comm_id}")
    assert del_resp.status_code == 204

    # Verify 404
    get_resp = await auth_client.get(f"/api/v1/client-communications/{comm_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_ai_draft_communication(
    auth_client: AsyncClient, create_test_client, create_test_project
):
    user_id = auth_client._test_user.id
    client = await create_test_client(user_id, name="Eta Analytics")
    project = await create_test_project(user_id, client_id=client.id, name="Data Pipeline")

    resp = await auth_client.post(
        "/api/v1/client-communications/ai-draft",
        json={
            "client_id": client.id,
            "project_id": project.id,
            "communication_type": "STATUS_UPDATE",
            "tone": "professional",
            "context_notes": "Completed phase 1 data ingestion; phase 2 modeling is starting.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "DRAFT"
    assert data["client_id"] == client.id
    assert data["project_id"] == project.id
    assert data["subject"] is not None
    assert len(data["content"]) > 0

