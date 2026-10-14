"""Every non-GitHub agent tool must run against the real services (no mocks).

Earlier, task.search / project.list / client.list called service methods that did not exist.
"""

import pytest

from app.agent.tools.base import ToolContext, ToolPermission
from app.agent.tools.registry import create_default_registry
from app.api.deps import get_agent_orchestrator


@pytest.fixture
async def setup(auth_client, db_session, create_test_client, create_test_project, create_test_task):
    user = auth_client._test_user
    client = await create_test_client(user.id, name="Globex")
    project = await create_test_project(user.id, client.id, name="Portal")
    task = await create_test_task(user.id, project_id=project.id, title="Design login")
    analysis = await auth_client.post(
        "/api/v1/requirements/", json={"project_id": project.id, "title": "Portal v1", "brief": "Customer portal."}
    )
    orchestrator = await get_agent_orchestrator(db_session)
    context = ToolContext(user=user, execution_id="test", extra=orchestrator.extra_services)
    ids = {"client": client.id, "project": project.id, "task": task.id, "analysis": analysis.json()["id"]}
    return context, ids


def _inputs(ids):
    return {
        "task.search": {"search": "login", "limit": 5},
        "task.get": {"task_id": ids["task"]},
        "project.list": {"status": "ACTIVE"},
        "project.get": {"project_id": ids["project"]},
        "client.list": {},
        "client.get": {"client_id": ids["client"]},
        "requirements.get_analysis": {"analysis_id": ids["analysis"]},
        "requirements.list_for_project": {"project_id": ids["project"]},
    }


async def test_all_read_tools_run_against_real_services(setup):
    context, ids = setup
    registry = create_default_registry()
    inputs = _inputs(ids)
    read_tools = {
        t.name
        for t in registry.list_by_permission(ToolPermission.READ)
        if not t.name.startswith("github.")  # needs a real GitHub account
    }

    assert read_tools <= set(inputs), f"add inputs for new tools: {read_tools - set(inputs)}"
    for name in sorted(read_tools):
        result = await registry.get(name).execute(dict(inputs[name]), context)
        assert result.success, f"{name} failed: {result.error}"

    found = await registry.get("task.search").execute({"search": "login"}, context)
    assert [t["title"] for t in found.data["tasks"]] == ["Design login"]


async def test_write_tools_run_against_real_services(setup, auth_client):
    context, ids = setup
    registry = create_default_registry()

    async def run(name, data):
        result = await registry.get(name).execute(data, context)
        assert result.success, f"{name} failed: {result.error}"
        return result.data

    created = await run("task.create", {"title": "Ship it", "project_id": ids["project"], "due_date": "2026-12-01"})
    await run("task.update", {"task_id": created["task_id"], "title": "Ship it now"})
    await run("task.change_status", {"task_id": created["task_id"], "status": "IN_PROGRESS"})
    await run("task.change_priority", {"task_id": created["task_id"], "priority": "URGENT"})

    task = (await auth_client.get(f"/api/v1/tasks/{created['task_id']}")).json()
    assert (task["title"], task["status"], task["priority"]) == ("Ship it now", "IN_PROGRESS", "URGENT")
    assert task["project_id"] == ids["project"] and task["due_date"] == "2026-12-01"


async def test_tools_cannot_touch_another_users_records(setup, create_test_user, create_test_task):
    context, _ = setup
    other, _ = await create_test_user(email="other@example.com")
    foreign = await create_test_task(other.id, title="Not yours")
    registry = create_default_registry()

    for name, data in [
        ("task.get", {"task_id": foreign.id}),
        ("task.change_status", {"task_id": foreign.id, "status": "COMPLETED"}),
    ]:
        result = await registry.get(name).execute(data, context)
        assert not result.success, f"{name} reached another user's task"
