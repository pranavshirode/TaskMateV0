"""Tests for milestones and task dependencies."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_milestone(auth_client: AsyncClient, create_test_project):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    resp = await auth_client.post(
        "/api/v1/milestones",
        json={"project_id": project.id, "title": "MVP Release", "status": "OPEN"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "MVP Release"
    assert data["status"] == "OPEN"
    assert data["project_id"] == project.id


@pytest.mark.asyncio
async def test_create_milestone_wrong_project(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v1/milestones",
        json={"project_id": "nonexistent-id", "title": "Bad Milestone"},
    )
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_list_milestones(auth_client: AsyncClient, create_test_project):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    for title in ("Alpha", "Beta"):
        resp = await auth_client.post(
            "/api/v1/milestones",
            json={"project_id": project.id, "title": title},
        )
        assert resp.status_code == 201

    resp = await auth_client.get(f"/api/v1/milestones/project/{project.id}")
    assert resp.status_code == 200
    items = resp.json()
    titles = [m["title"] for m in items]
    assert "Alpha" in titles
    assert "Beta" in titles


@pytest.mark.asyncio
async def test_update_milestone(auth_client: AsyncClient, create_test_project):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    create_resp = await auth_client.post(
        "/api/v1/milestones",
        json={"project_id": project.id, "title": "To Update"},
    )
    assert create_resp.status_code == 201
    mid = create_resp.json()["id"]

    resp = await auth_client.patch(
        f"/api/v1/milestones/{mid}",
        json={"status": "COMPLETED", "title": "Updated Title"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_milestone(auth_client: AsyncClient, create_test_project):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    create_resp = await auth_client.post(
        "/api/v1/milestones",
        json={"project_id": project.id, "title": "To Delete"},
    )
    assert create_resp.status_code == 201
    mid = create_resp.json()["id"]

    resp = await auth_client.delete(f"/api/v1/milestones/{mid}")
    assert resp.status_code == 204

    get_resp = await auth_client.get(f"/api/v1/milestones/{mid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_status(auth_client: AsyncClient, create_test_project):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    resp = await auth_client.post(
        "/api/v1/milestones",
        json={"project_id": project.id, "title": "Bad Status", "status": "INVALID"},
    )
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
class TestTaskDependencies:
    async def _create_task(self, auth_client: AsyncClient, project_id: str, title: str) -> str:
        resp = await auth_client.post(
            "/api/v1/tasks/",
            json={"title": title, "project_id": project_id, "status": "TODO", "priority": "MEDIUM"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    async def test_add_dependency(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "Task A")
        t2 = await self._create_task(auth_client, project.id, "Task B")

        resp = await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["task_id"] == t2
        assert data["depends_on_task_id"] == t1

    async def test_self_dependency_rejected(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "Task Self")
        resp = await auth_client.post(
            f"/api/v1/tasks/{t1}/dependencies",
            json={"depends_on_task_id": t1},
        )
        assert resp.status_code == 422

    async def test_cycle_rejected(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "Cycle Task 1")
        t2 = await self._create_task(auth_client, project.id, "Cycle Task 2")

        # t2 depends on t1
        resp1 = await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )
        assert resp1.status_code == 201

        # t1 depends on t2 -> cycle -> should be rejected
        resp = await auth_client.post(
            f"/api/v1/tasks/{t1}/dependencies",
            json={"depends_on_task_id": t2},
        )
        assert resp.status_code == 422

    async def test_duplicate_dependency_rejected(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "Dup Task 1")
        t2 = await self._create_task(auth_client, project.id, "Dup Task 2")

        resp1 = await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )
        assert resp1.status_code == 201

        resp = await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )
        assert resp.status_code == 409

    async def test_list_dependencies(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "List Dep T1")
        t2 = await self._create_task(auth_client, project.id, "List Dep T2")

        await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )

        resp = await auth_client.get(f"/api/v1/tasks/{t2}/dependencies")
        assert resp.status_code == 200
        deps = resp.json()
        assert len(deps) == 1
        assert deps[0]["depends_on_task_id"] == t1

    async def test_remove_dependency(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        t1 = await self._create_task(auth_client, project.id, "Remove Dep T1")
        t2 = await self._create_task(auth_client, project.id, "Remove Dep T2")

        await auth_client.post(
            f"/api/v1/tasks/{t2}/dependencies",
            json={"depends_on_task_id": t1},
        )
        resp = await auth_client.delete(f"/api/v1/tasks/{t2}/dependencies/{t1}")
        assert resp.status_code == 204

        # Verify removed
        list_resp = await auth_client.get(f"/api/v1/tasks/{t2}/dependencies")
        assert list_resp.json() == []
