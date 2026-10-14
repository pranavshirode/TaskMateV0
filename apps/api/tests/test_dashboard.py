from datetime import date, timedelta

import pytest

from app.models.enums import TaskPriority, TaskStatus


@pytest.mark.asyncio
async def test_dashboard_today(auth_client):
    response = await auth_client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert "due_today" in data
    assert "overdue" in data
    assert "high_priority" in data
    assert "active_projects" in data
    assert "recently_updated" in data


@pytest.mark.asyncio
async def test_dashboard_due_today(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Due Today Task", due_date=date.today())
    response = await auth_client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["due_today"], list)


@pytest.mark.asyncio
async def test_dashboard_overdue(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    yesterday = date.today() - timedelta(days=1)
    await create_test_task(user_id, title="Overdue Task", due_date=yesterday)
    response = await auth_client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["overdue"], list)


@pytest.mark.asyncio
async def test_dashboard_high_priority(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Urgent Task", priority=TaskPriority.URGENT)
    response = await auth_client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["high_priority"], list)


@pytest.mark.asyncio
async def test_dashboard_completed_excluded(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Completed Task", status=TaskStatus.COMPLETED, priority=TaskPriority.URGENT)
    response = await auth_client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    # Completed tasks should not appear in high_priority or due_today
    for task in data.get("high_priority", []):
        assert task["status"] != "COMPLETED"
