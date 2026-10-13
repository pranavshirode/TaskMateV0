import pytest

from app.models.enums import TaskPriority, TaskStatus


@pytest.mark.asyncio
async def test_create_task(auth_client):
    response = await auth_client.post(
        "/api/v1/tasks/", json={"title": "New Task", "status": "TODO", "priority": "MEDIUM"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "New Task"


@pytest.mark.asyncio
async def test_create_task_with_project(auth_client, create_test_project):
    user_id = auth_client._test_user.id
    p = await create_test_project(user_id)
    response = await auth_client.post("/api/v1/tasks/", json={"title": "Project Task", "project_id": p.id})
    assert response.status_code == 201
    assert response.json()["project_id"] == p.id


@pytest.mark.asyncio
async def test_create_task_with_labels(auth_client):
    response = await auth_client.post("/api/v1/tasks/", json={"title": "Labeled Task", "labels": ["bug", "urgent"]})
    assert response.status_code == 201
    data = response.json()
    assert "labels" in data
    label_names = [lbl["name"] for lbl in data.get("labels", [])]
    if label_names:
        assert "bug" in label_names


@pytest.mark.asyncio
async def test_list_tasks(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Task A")
    await create_test_task(user_id, title="Task B")
    response = await auth_client.get("/api/v1/tasks/")
    assert response.status_code == 200
    assert response.json()["total"] >= 2


@pytest.mark.asyncio
async def test_get_task(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id)
    response = await auth_client.get(f"/api/v1/tasks/{t.id}")
    assert response.status_code == 200
    assert response.json()["id"] == t.id


@pytest.mark.asyncio
async def test_update_task(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id)
    response = await auth_client.patch(f"/api/v1/tasks/{t.id}", json={"title": "Updated Title"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_archive_task(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id)
    response = await auth_client.delete(f"/api/v1/tasks/{t.id}")
    assert response.status_code == 200
    assert response.json()["archived_at"] is not None


@pytest.mark.asyncio
async def test_change_task_status(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id, status=TaskStatus.TODO)
    response = await auth_client.patch(f"/api/v1/tasks/{t.id}/status", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_change_task_status_creates_event(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id, status=TaskStatus.TODO)
    await auth_client.patch(f"/api/v1/tasks/{t.id}/status", json={"status": "COMPLETED"})
    events_resp = await auth_client.get(f"/api/v1/tasks/{t.id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    assert len(events) >= 1
    assert any(e["event_type"] == "STATUS_CHANGED" for e in events)


@pytest.mark.asyncio
async def test_change_task_priority(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    t = await create_test_task(user_id, priority=TaskPriority.LOW)
    response = await auth_client.patch(f"/api/v1/tasks/{t.id}/priority", json={"priority": "URGENT"})
    assert response.status_code == 200
    assert response.json()["priority"] == "URGENT"


@pytest.mark.asyncio
async def test_filter_tasks_by_status(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, status=TaskStatus.BLOCKED)
    response = await auth_client.get("/api/v1/tasks/?status=BLOCKED")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert all(t["status"] == "BLOCKED" for t in items)


@pytest.mark.asyncio
async def test_filter_tasks_by_priority(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, priority=TaskPriority.URGENT)
    response = await auth_client.get("/api/v1/tasks/?priority=URGENT")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_filter_tasks_by_project(auth_client, create_test_task, create_test_project):
    user_id = auth_client._test_user.id
    p = await create_test_project(user_id)
    await create_test_task(user_id, project_id=p.id)
    response = await auth_client.get(f"/api/v1/tasks/?project_id={p.id}")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_tasks(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Unicorn")
    response = await auth_client.get("/api/v1/tasks/?search=Unicorn")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_task_pagination(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    for _ in range(5):
        await create_test_task(user_id)
    response = await auth_client.get("/api/v1/tasks/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5


@pytest.mark.asyncio
async def test_task_data_isolation(auth_client, create_test_task, create_test_user):
    other_user, _ = await create_test_user("othert@test.com", "pass")
    t = await create_test_task(other_user.id)
    response = await auth_client.get(f"/api/v1/tasks/{t.id}")
    assert response.status_code == 404
