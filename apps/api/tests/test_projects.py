import pytest


@pytest.mark.asyncio
async def test_create_project(auth_client):
    response = await auth_client.post("/api/v1/projects/", json={"name": "New Project", "status": "PLANNING"})
    assert response.status_code == 201
    assert response.json()["name"] == "New Project"


@pytest.mark.asyncio
async def test_create_project_with_client(auth_client, create_test_client_entity):
    user_id = auth_client._test_user.id
    c = await create_test_client_entity(user_id, "Project Client")
    response = await auth_client.post("/api/v1/projects/", json={"name": "Client Project", "client_id": c.id})
    assert response.status_code == 201
    assert response.json()["client_id"] == c.id


@pytest.mark.asyncio
async def test_list_projects(auth_client, create_test_project):
    user_id = auth_client._test_user.id
    await create_test_project(user_id, name="Project 1")
    await create_test_project(user_id, name="Project 2")
    response = await auth_client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert response.json()["total"] >= 2


@pytest.mark.asyncio
async def test_get_project_detail(auth_client, create_test_project, create_test_task):
    user_id = auth_client._test_user.id
    p = await create_test_project(user_id, name="Detail Project")
    await create_test_task(user_id, project_id=p.id, title="Task 1")
    response = await auth_client.get(f"/api/v1/projects/{p.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == p.id
    assert "task_summary" in data


@pytest.mark.asyncio
async def test_update_project(auth_client, create_test_project):
    user_id = auth_client._test_user.id
    p = await create_test_project(user_id, name="Update Project")
    response = await auth_client.patch(f"/api/v1/projects/{p.id}", json={"name": "Updated Project"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"


@pytest.mark.asyncio
async def test_archive_project(auth_client, create_test_project):
    user_id = auth_client._test_user.id
    p = await create_test_project(user_id, name="Archive Project")
    response = await auth_client.delete(f"/api/v1/projects/{p.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_filter_projects_by_status(auth_client, create_test_project):
    user_id = auth_client._test_user.id
    await create_test_project(user_id, name="P1")  # default ACTIVE
    response = await auth_client.get("/api/v1/projects/?status=ACTIVE")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    response = await auth_client.get("/api/v1/projects/?status=COMPLETED")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_filter_projects_by_client(auth_client, create_test_project, create_test_client_entity):
    user_id = auth_client._test_user.id
    c1 = await create_test_client_entity(user_id, "C1")
    c2 = await create_test_client_entity(user_id, "C2")
    await create_test_project(user_id, client_id=c1.id, name="P1")
    await create_test_project(user_id, client_id=c2.id, name="P2")
    response = await auth_client.get(f"/api/v1/projects/?client_id={c1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["client_id"] == c1.id


@pytest.mark.asyncio
async def test_project_data_isolation(auth_client, create_test_project, create_test_user):
    other_user, _ = await create_test_user("otherp@test.com", "pass")
    p = await create_test_project(other_user.id, name="Other User Project")
    response = await auth_client.get(f"/api/v1/projects/{p.id}")
    assert response.status_code == 404
