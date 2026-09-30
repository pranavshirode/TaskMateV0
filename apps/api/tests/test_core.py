import pytest


class TestTaskEndpoints:
    @pytest.mark.asyncio
    async def test_create_task(self, auth_client):
        res = await auth_client.post("/api/v1/tasks", json={
            "title": "My First Task", "priority": "HIGH"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "My First Task"
        assert data["priority"] == "HIGH"
        assert data["status"] == "TODO"

    @pytest.mark.asyncio
    async def test_list_tasks(self, auth_client):
        await auth_client.post("/api/v1/tasks", json={"title": "Task 1"})
        await auth_client.post("/api/v1/tasks", json={"title": "Task 2"})
        res = await auth_client.get("/api/v1/tasks")
        assert res.status_code == 200
        assert res.json()["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_task(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "Detail Task"})
        task_id = create_res.json()["id"]
        res = await auth_client.get(f"/api/v1/tasks/{task_id}")
        assert res.status_code == 200
        assert res.json()["title"] == "Detail Task"

    @pytest.mark.asyncio
    async def test_update_task(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "Old"})
        task_id = create_res.json()["id"]
        res = await auth_client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New"})
        assert res.status_code == 200
        assert res.json()["title"] == "New"

    @pytest.mark.asyncio
    async def test_change_status(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "Status Task"})
        task_id = create_res.json()["id"]
        res = await auth_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "IN_PROGRESS"})
        assert res.status_code == 200
        assert res.json()["status"] == "IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_change_priority(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "Priority Task"})
        task_id = create_res.json()["id"]
        res = await auth_client.patch(f"/api/v1/tasks/{task_id}/priority", json={"priority": "URGENT"})
        assert res.status_code == 200
        assert res.json()["priority"] == "URGENT"

    @pytest.mark.asyncio
    async def test_archive_task(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "To Archive"})
        task_id = create_res.json()["id"]
        res = await auth_client.delete(f"/api/v1/tasks/{task_id}")
        assert res.status_code == 200
        assert res.json()["archived_at"] is not None

    @pytest.mark.asyncio
    async def test_task_events(self, auth_client):
        create_res = await auth_client.post("/api/v1/tasks", json={"title": "Events Task"})
        task_id = create_res.json()["id"]
        # Change status to generate an event
        await auth_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "IN_PROGRESS"})
        res = await auth_client.get(f"/api/v1/tasks/{task_id}/events")
        assert res.status_code == 200
        events = res.json()
        assert events["total"] >= 1

    @pytest.mark.asyncio
    async def test_filter_by_status(self, auth_client):
        await auth_client.post("/api/v1/tasks", json={"title": "Backlog Task", "status": "BACKLOG"})
        res = await auth_client.get("/api/v1/tasks?status=BACKLOG")
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["status"] == "BACKLOG"

    @pytest.mark.asyncio
    async def test_filter_by_priority(self, auth_client):
        await auth_client.post("/api/v1/tasks", json={"title": "Urgent Task", "priority": "URGENT"})
        res = await auth_client.get("/api/v1/tasks?priority=URGENT")
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["priority"] == "URGENT"

    @pytest.mark.asyncio
    async def test_search_tasks(self, auth_client):
        await auth_client.post("/api/v1/tasks", json={"title": "UniqueSearchTitle"})
        res = await auth_client.get("/api/v1/tasks?search=UniqueSearchTitle")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_task_data_isolation(self, client, create_test_user):
        user1, token1 = await create_test_user(email="iso1@test.com")
        client.headers["Authorization"] = f"Bearer {token1}"
        res = await client.post("/api/v1/tasks", json={"title": "User1 Task"})
        task_id = res.json()["id"]

        user2, token2 = await create_test_user(email="iso2@test.com")
        client.headers["Authorization"] = f"Bearer {token2}"
        res = await client.get(f"/api/v1/tasks/{task_id}")
        assert res.status_code in [404, 400, 403]


class TestProjectEndpoints:
    @pytest.mark.asyncio
    async def test_create_project(self, auth_client):
        res = await auth_client.post("/api/v1/projects", json={
            "name": "My Project", "status": "PLANNING"
        })
        assert res.status_code == 201
        assert res.json()["name"] == "My Project"

    @pytest.mark.asyncio
    async def test_list_projects(self, auth_client):
        await auth_client.post("/api/v1/projects", json={"name": "Proj A"})
        res = await auth_client.get("/api/v1/projects")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_project_detail(self, auth_client):
        create_res = await auth_client.post("/api/v1/projects", json={"name": "Detail Proj"})
        proj_id = create_res.json()["id"]
        res = await auth_client.get(f"/api/v1/projects/{proj_id}")
        assert res.status_code == 200
        assert "task_summary" in res.json()

    @pytest.mark.asyncio
    async def test_archive_project(self, auth_client):
        create_res = await auth_client.post("/api/v1/projects", json={"name": "To Archive"})
        proj_id = create_res.json()["id"]
        res = await auth_client.delete(f"/api/v1/projects/{proj_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "ARCHIVED"


class TestDashboardEndpoints:
    @pytest.mark.asyncio
    async def test_get_dashboard(self, auth_client):
        res = await auth_client.get("/api/v1/dashboard/today")
        assert res.status_code == 200
        data = res.json()
        assert "due_today" in data
        assert "overdue" in data
        assert "high_priority" in data
        assert "active_projects" in data
        assert "recently_updated" in data


class TestLabelEndpoints:
    @pytest.mark.asyncio
    async def test_create_label(self, auth_client):
        res = await auth_client.post("/api/v1/labels", json={"name": "bug", "color": "#ff0000"})
        assert res.status_code == 201
        assert res.json()["name"] == "bug"

    @pytest.mark.asyncio
    async def test_list_labels(self, auth_client):
        await auth_client.post("/api/v1/labels", json={"name": "feature"})
        res = await auth_client.get("/api/v1/labels")
        assert res.status_code == 200
        assert len(res.json()) >= 1
