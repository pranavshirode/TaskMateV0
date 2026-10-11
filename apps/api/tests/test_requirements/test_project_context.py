"""Integration tests for Project Context Notes and Structured Memory."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_context_memory_lifecycle(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
):
    user, token = await create_test_user(email="context_user@example.com")
    cl = await create_test_client(user.id)
    proj = await create_test_project(user.id, cl.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a confirmed architectural decision note
    create_resp = await client.post(
        f"/api/v1/projects/{proj.id}/context",
        headers=headers,
        json={
            "title": "Database Choice",
            "content": "Selected PostgreSQL with SQLAlchemy async engine and connection pooling.",
            "category": "DECISION",
            "source": "DEVELOPER_NOTE",
            "is_confirmed": True,
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    note = create_resp.json()
    note_id = note["id"]
    assert note["title"] == "Database Choice"
    assert note["is_confirmed"] is True
    assert note["is_superseded"] is False

    # 2. List context notes
    list_resp = await client.get(
        f"/api/v1/projects/{proj.id}/context",
        headers=headers,
    )
    assert list_resp.status_code == 200
    notes = list_resp.json()
    assert len(notes) == 1

    # 3. Update the note
    update_resp = await client.put(
        f"/api/v1/context/{note_id}",
        headers=headers,
        json={
            "title": "Database Architecture Choice",
            "content": "Selected PostgreSQL with PgBouncer connection pooling.",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Database Architecture Choice"

    # 4. Mark note as superseded
    update_sup = await client.put(
        f"/api/v1/context/{note_id}",
        headers=headers,
        json={"is_superseded": True},
    )
    assert update_sup.status_code == 200
    assert update_sup.json()["is_superseded"] is True

    # 5. Active list excludes superseded notes by default
    active_resp = await client.get(
        f"/api/v1/projects/{proj.id}/context",
        headers=headers,
    )
    assert active_resp.status_code == 200
    assert len(active_resp.json()) == 0

    # 6. Listing with include_superseded=True includes it
    all_resp = await client.get(
        f"/api/v1/projects/{proj.id}/context?include_superseded=true",
        headers=headers,
    )
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 1

    # 7. Delete note
    del_resp = await client.delete(
        f"/api/v1/context/{note_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204

