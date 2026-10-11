import pytest
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.services.orchestrator import AIOrchestrator
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.services.project import ProjectService
from app.services.task import TaskService


@pytest.mark.asyncio
async def test_orchestrator_create_task(db_session, create_test_user):
    user, _ = await create_test_user("orch_user@example.com")
    project_service = ProjectService(db_session)
    proj = await project_service.create(user.id, ProjectCreate(name="Acme website"))

    orchestrator = AIOrchestrator(db=db_session, provider=MockAIProvider())
    response = await orchestrator.chat(
        user_id=user.id,
        message="Create a high priority task for Acme website to fix the login bug due tomorrow",
    )

    assert response.intent == "CREATE_TASK"
    assert len(response.actions) == 1
    assert response.actions[0].type == "TASK_CREATED"
    assert "Fix the login bug" in response.message or "Fix login bug" in response.message or "login bug" in response.message.lower()

    # Verify task was actually created in DB via service
    task_service = TaskService(db_session)
    tasks = await task_service.list(user_id=user.id)
    assert tasks.total == 1
    assert tasks.items[0].priority == TaskPriority.HIGH
    assert tasks.items[0].project_id == proj.id


@pytest.mark.asyncio
async def test_orchestrator_complete_task(db_session, create_test_user):
    user, _ = await create_test_user("orch_comp@example.com")
    task_service = TaskService(db_session)
    task = await task_service.create(
        user.id, TaskCreate(title="Fix login bug", status=TaskStatus.IN_PROGRESS)
    )

    orchestrator = AIOrchestrator(db=db_session, provider=MockAIProvider())
    response = await orchestrator.chat(
        user_id=user.id,
        message="Mark the login bug task as completed",
    )

    assert response.intent == "COMPLETE_TASK"
    assert len(response.actions) == 1
    assert response.actions[0].type == "TASK_COMPLETED"

    # Verify task status in DB
    refreshed = await task_service.get(user_id=user.id, task_id=task.id)
    assert refreshed.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_orchestrator_today_tasks(db_session, create_test_user):
    user, _ = await create_test_user("orch_today@example.com")
    orchestrator = AIOrchestrator(db=db_session, provider=MockAIProvider())
    response = await orchestrator.chat(
        user_id=user.id,
        message="What's on my plate today?",
    )

    assert response.intent == "GET_TODAY_TASKS"
    assert "today" in response.message.lower()

