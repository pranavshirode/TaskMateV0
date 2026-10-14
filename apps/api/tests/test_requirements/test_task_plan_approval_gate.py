"""Tasks may only be created from an APPROVED requirements analysis (audit BUG-04)."""


async def _analyzed(auth_client, create_test_project):
    project = await create_test_project(auth_client._test_user.id)
    created = await auth_client.post(
        "/api/v1/requirements/",
        json={"project_id": project.id, "title": "Shop", "brief": "Online shop with cart and Stripe checkout."},
    )
    analysis_id = created.json()["id"]
    await auth_client.post(f"/api/v1/requirements/{analysis_id}/analyze")
    plan = await auth_client.post(f"/api/v1/requirements/{analysis_id}/generate-task-plan")
    return project, analysis_id, plan.json()["proposed_tasks"][:2]


async def test_unapproved_analysis_cannot_create_tasks(auth_client, create_test_project):
    project, analysis_id, tasks = await _analyzed(auth_client, create_test_project)

    resp = await auth_client.post(
        f"/api/v1/requirements/{analysis_id}/approve-task-plan", json={"selected_tasks": tasks}
    )

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ANALYSIS_NOT_APPROVED"
    listed = await auth_client.get("/api/v1/tasks/", params={"project_id": project.id})
    assert listed.json()["total"] == 0


async def test_approved_analysis_creates_tasks(auth_client, create_test_project):
    project, analysis_id, tasks = await _analyzed(auth_client, create_test_project)
    await auth_client.post(f"/api/v1/requirements/{analysis_id}/approve")

    resp = await auth_client.post(
        f"/api/v1/requirements/{analysis_id}/approve-task-plan", json={"selected_tasks": tasks}
    )

    assert resp.status_code == 200
    assert resp.json()["created_tasks_count"] == len(tasks)
