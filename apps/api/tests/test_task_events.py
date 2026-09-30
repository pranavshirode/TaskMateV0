import pytest
from app.models.enums import TaskStatus, TaskPriority

@pytest.mark.asyncio
async def test_task_creation_creates_event(auth_client):
    res = await auth_client.post("/api/v1/tasks/", json={"title": "Event Task"})
    assert res.status_code == 201
    task_id = res.json()["id"]
    events_res = await auth_client.get(f"/api/v1/tasks/{task_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()["items"]
    assert any(e["event_type"] == "TASK_CREATED" for e in events)

@pytest.mark.asyncio
async def test_status_change_creates_event(auth_client):
    res = await auth_client.post("/api/v1/tasks/", json={"title": "Status Event Task"})
    task_id = res.json()["id"]
    await auth_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "IN_PROGRESS"})
    events_res = await auth_client.get(f"/api/v1/tasks/{task_id}/events")
    events = events_res.json()["items"]
    assert any(e["event_type"] == "STATUS_CHANGED" for e in events)

@pytest.mark.asyncio
async def test_priority_change_creates_event(auth_client):
    res = await auth_client.post("/api/v1/tasks/", json={"title": "Priority Event Task"})
    task_id = res.json()["id"]
    await auth_client.patch(f"/api/v1/tasks/{task_id}/priority", json={"priority": "URGENT"})
    events_res = await auth_client.get(f"/api/v1/tasks/{task_id}/events")
    events = events_res.json()["items"]
    assert any(e["event_type"] == "PRIORITY_CHANGED" for e in events)

@pytest.mark.asyncio
async def test_list_task_events(auth_client):
    res = await auth_client.post("/api/v1/tasks/", json={"title": "List Events Task"})
    task_id = res.json()["id"]
    response = await auth_client.get(f"/api/v1/tasks/{task_id}/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
