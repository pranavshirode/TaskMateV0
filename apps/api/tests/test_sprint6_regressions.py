"""Regression tests for audit BUG-14 (dashboard progress) and BUG-16 (foreign repository -> 404)."""

from app.models.enums import TaskStatus


async def test_dashboard_active_projects_include_task_summary(auth_client, create_test_project, create_test_task):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id)
    await create_test_task(user_id, project_id=project.id, status=TaskStatus.COMPLETED)
    await create_test_task(user_id, project_id=project.id)

    projects = (await auth_client.get("/api/v1/dashboard/today")).json()["active_projects"]

    assert projects[0]["task_summary"]["total"] == 2
    assert projects[0]["task_summary"]["completed"] == 1


async def test_other_users_repository_is_not_found(client, create_test_user, create_test_project):
    owner, owner_token = await create_test_user(email="owner@example.com")
    _, other_token = await create_test_user(email="other@example.com")
    project = await create_test_project(owner.id)
    repo = (
        await client.post(
            f"/api/v1/projects/{project.id}/repositories",
            json={"name": "api", "url": "https://github.com/a/api", "provider": "GITHUB", "default_branch": "main"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
    ).json()
    other = {"Authorization": f"Bearer {other_token}"}

    assert (await client.get(f"/api/v1/repositories/{repo['id']}", headers=other)).status_code == 404
    assert (await client.delete(f"/api/v1/repositories/{repo['id']}", headers=other)).status_code == 404
    created = await client.post(
        f"/api/v1/projects/{project.id}/repositories",
        json={"name": "x", "url": "https://github.com/a/x"},
        headers=other,
    )
    assert created.status_code == 404
