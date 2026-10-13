from datetime import date, timedelta

import pytest

from app.ai.context.builder import AIContextBuilder
from app.ai.context.resolver import EntityResolver
from app.models.enums import TaskPriority, TaskStatus


def test_entity_resolver_dates():
    today = date(2026, 10, 1)
    assert EntityResolver.resolve_date("today", today) == today
    assert EntityResolver.resolve_date("tomorrow", today) == today + timedelta(days=1)
    assert EntityResolver.resolve_date("next week", today) == today + timedelta(days=7)
    assert EntityResolver.resolve_date("2026-10-15", today) == date(2026, 10, 15)
    assert EntityResolver.resolve_date("invalid-date", today) is None


def test_entity_resolver_priority_and_status():
    assert EntityResolver.resolve_priority("urgent") == TaskPriority.URGENT
    assert EntityResolver.resolve_priority("high priority") == TaskPriority.HIGH
    assert EntityResolver.resolve_priority("low") == TaskPriority.LOW
    assert EntityResolver.resolve_priority(None) == TaskPriority.MEDIUM

    assert EntityResolver.resolve_status("in_progress") == TaskStatus.IN_PROGRESS
    assert EntityResolver.resolve_status("done") == TaskStatus.COMPLETED
    assert EntityResolver.resolve_status("blocked") == TaskStatus.BLOCKED
    assert EntityResolver.resolve_status(None) == TaskStatus.TODO


def test_entity_resolver_fuzzy_matching():
    projects = [
        {"id": "p-1", "name": "Acme Website"},
        {"id": "p-2", "name": "Mobile App API"},
    ]
    # Exact / case-insensitive
    match, ambig = EntityResolver.match_item("acme website", projects, "name")
    assert match is not None
    assert match["id"] == "p-1"

    # Substring
    match, ambig = EntityResolver.match_item("Mobile App", projects, "name")
    assert match is not None
    assert match["id"] == "p-2"

    # Ambiguity check
    multi_items = [
        {"id": "p-1", "name": "Acme Backend"},
        {"id": "p-2", "name": "Acme Frontend"},
    ]
    match, ambig = EntityResolver.match_item("Acme", multi_items, "name")
    assert match is None
    assert len(ambig) == 2


@pytest.mark.asyncio
async def test_context_builder_user_isolation(db_session, create_test_user):
    user1, _ = await create_test_user("user1@example.com")
    user2, _ = await create_test_user("user2@example.com")

    # Create project for user1
    from app.schemas.project import ProjectCreate
    from app.services.project import ProjectService

    ps = ProjectService(db_session)
    await ps.create(user1.id, ProjectCreate(name="User1 Secret Project"))

    # Build context for user2
    cb = AIContextBuilder(db_session)
    context_user2 = await cb.build(user2.id)

    # Verify user2 context does not see user1's project
    assert len(context_user2.projects) == 0
    assert "User1 Secret Project" not in context_user2.to_prompt_text()
