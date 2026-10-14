"""
End-to-end test workflows as specified in Sprint 1 requirements.

Workflow 1: Developer registers → creates client → creates project → creates task → updates status → views dashboard
Workflow 2: Developer creates multiple tasks → filters/searches → archives → verifies archived hidden
Workflow 3: Developer creates project → adds repository → creates tasks → views project detail with summary
"""

import pytest


class TestWorkflow1_FullDevLoop:
    """Register → Client → Project → Task → Status → Dashboard"""

    @pytest.mark.asyncio
    async def test_full_developer_workflow(self, client):
        # 1. Register
        reg = await client.post(
            "/api/v1/auth/register", json={"name": "Dev User", "email": "dev@workflow.com", "password": "workflow123"}
        )
        assert reg.status_code == 201

        # 2. Login
        login = await client.post("/api/v1/auth/login", json={"email": "dev@workflow.com", "password": "workflow123"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"

        # 3. Create client
        cl = await client.post("/api/v1/clients", json={"name": "Acme Corp", "company_name": "Acme Inc."})
        assert cl.status_code == 201
        client_id = cl.json()["id"]

        # 4. Create project
        proj = await client.post(
            "/api/v1/projects", json={"name": "Acme Dashboard", "client_id": client_id, "status": "ACTIVE"}
        )
        assert proj.status_code == 201
        project_id = proj.json()["id"]

        # 5. Create task
        task = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Build login page",
                "project_id": project_id,
                "client_id": client_id,
                "priority": "HIGH",
                "status": "TODO",
            },
        )
        assert task.status_code == 201
        task_id = task.json()["id"]

        # 6. Update status to IN_PROGRESS
        status_res = await client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "IN_PROGRESS"})
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "IN_PROGRESS"

        # 7. Update status to COMPLETED
        status_res = await client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "COMPLETED"})
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "COMPLETED"
        assert status_res.json()["completed_at"] is not None

        # 8. Check events
        events = await client.get(f"/api/v1/tasks/{task_id}/events")
        assert events.status_code == 200
        assert events.json()["total"] >= 2  # created + status changes

        # 9. View dashboard
        dash = await client.get("/api/v1/dashboard/today")
        assert dash.status_code == 200
        data = dash.json()
        assert "due_today" in data
        assert "active_projects" in data


class TestWorkflow2_FilterAndArchive:
    """Multiple tasks → filter → search → archive → verify hidden"""

    @pytest.mark.asyncio
    async def test_filter_search_archive_workflow(self, auth_client):
        # Create multiple tasks
        for i in range(5):
            await auth_client.post(
                "/api/v1/tasks",
                json={
                    "title": f"Workflow Task {i}",
                    "priority": "HIGH" if i % 2 == 0 else "LOW",
                    "status": "TODO" if i < 3 else "BACKLOG",
                },
            )

        # Filter by status
        res = await auth_client.get("/api/v1/tasks?status=TODO")
        assert res.status_code == 200
        todo_count = res.json()["total"]
        assert todo_count >= 3

        # Filter by priority
        res = await auth_client.get("/api/v1/tasks?priority=HIGH")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

        # Search
        res = await auth_client.get("/api/v1/tasks?search=Workflow+Task+0")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

        # Archive first task
        all_tasks = await auth_client.get("/api/v1/tasks")
        first_id = all_tasks.json()["items"][0]["id"]
        archive_res = await auth_client.delete(f"/api/v1/tasks/{first_id}")
        assert archive_res.status_code == 200

        # Verify archived task not in default list
        after = await auth_client.get("/api/v1/tasks")
        ids = [t["id"] for t in after.json()["items"]]
        assert first_id not in ids


class TestWorkflow3_ProjectWithReposAndTasks:
    """Project → Repository → Tasks → Project Detail with summary"""

    @pytest.mark.asyncio
    async def test_project_repo_task_workflow(self, auth_client):
        # Create project
        proj = await auth_client.post("/api/v1/projects", json={"name": "Full Stack App", "status": "ACTIVE"})
        assert proj.status_code == 201
        project_id = proj.json()["id"]

        # Add repository
        repo = await auth_client.post(
            f"/api/v1/projects/{project_id}/repositories",
            json={
                "name": "fullstack-app",
                "url": "https://github.com/dev/fullstack-app",
                "provider": "GITHUB",
                "default_branch": "main",
            },
        )
        assert repo.status_code == 201
        repo_id = repo.json()["id"]

        # List repos
        repos = await auth_client.get(f"/api/v1/projects/{project_id}/repositories")
        assert len(repos.json()) >= 1

        # Create tasks for the project
        for title, status in [("Setup DB", "COMPLETED"), ("Build API", "IN_PROGRESS"), ("Write Tests", "TODO")]:
            await auth_client.post("/api/v1/tasks", json={"title": title, "project_id": project_id, "status": status})

        # Get project detail - should have task_summary
        detail = await auth_client.get(f"/api/v1/projects/{project_id}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["task_summary"]["total"] == 3
        assert data["task_summary"]["completed"] == 1
        assert data["task_summary"]["in_progress"] == 1

        # Get repo by id
        repo_detail = await auth_client.get(f"/api/v1/repositories/{repo_id}")
        assert repo_detail.status_code == 200

        # Delete repo
        del_res = await auth_client.delete(f"/api/v1/repositories/{repo_id}")
        assert del_res.status_code == 204
