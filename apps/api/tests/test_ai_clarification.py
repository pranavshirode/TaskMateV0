"""The assistant asks instead of inventing values (audit BUG-10/11), offline agent demo flow."""


async def test_chat_without_task_title_asks_and_creates_nothing(auth_client):
    resp = await auth_client.post("/api/v1/ai/chat", json={"message": "Create a task"})

    body = resp.json()
    assert resp.status_code == 200
    assert body["requires_clarification"] is True
    assert body["message"] == "What should the task be called?"
    assert (await auth_client.get("/api/v1/tasks/")).json()["total"] == 0


async def test_chat_ambiguous_reference_sets_clarification_flag(auth_client, create_test_task):
    user_id = auth_client._test_user.id
    await create_test_task(user_id, title="Fix login bug on iOS")
    await create_test_task(user_id, title="Fix login bug on Android")

    body = (await auth_client.post("/api/v1/ai/chat", json={"message": "Mark the login bug task as completed"})).json()

    assert body["requires_clarification"] is True
    statuses = {t["status"] for t in (await auth_client.get("/api/v1/tasks/")).json()["items"]}
    assert statuses == {"TODO"}


async def test_offline_agent_create_task_needs_approval_then_persists(auth_client):
    run = (
        await auth_client.post("/api/v1/agent/run", json={"prompt": "Create a task to review the invoice due tomorrow"})
    ).json()

    assert run["status"] == "WAITING_FOR_APPROVAL"
    assert run["pending_action"]["arguments"]["title"] == "Review the invoice"
    assert (await auth_client.get("/api/v1/tasks/")).json()["total"] == 0

    approved = (await auth_client.post(f"/api/v1/agent/executions/{run['execution_id']}/approve")).json()

    assert approved["status"] == "COMPLETED"
    tasks = (await auth_client.get("/api/v1/tasks/")).json()["items"]
    assert [t["title"] for t in tasks] == ["Review the invoice"]
    assert tasks[0]["due_date"] is not None


async def test_offline_agent_search_summarises_real_results(auth_client, create_test_task):
    await create_test_task(auth_client._test_user.id, title="Write API docs")

    run = (await auth_client.post("/api/v1/agent/run", json={"prompt": "Find tasks about API"})).json()

    assert run["status"] == "COMPLETED"
    assert "Write API docs" in run["message"]
