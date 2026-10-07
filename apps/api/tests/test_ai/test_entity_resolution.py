"""Tests for entity resolution."""
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.ai.context.resolver import (
    EntityResolver,
    ResolutionResult,
    ResolutionStatus,
    VALID_PRIORITIES,
    VALID_STATUSES,
)


class TestResolvePriority:
    def test_valid_priorities(self):
        for p in VALID_PRIORITIES:
            assert EntityResolver.resolve_priority(p) == p

    def test_case_insensitive(self):
        assert EntityResolver.resolve_priority("high") == "HIGH"
        assert EntityResolver.resolve_priority("Low") == "LOW"

    def test_aliases(self):
        assert EntityResolver.resolve_priority("urgent") == "URGENT"
        assert EntityResolver.resolve_priority("critical") == "URGENT"
        assert EntityResolver.resolve_priority("important") == "HIGH"
        assert EntityResolver.resolve_priority("normal") == "MEDIUM"

    def test_invalid_returns_none(self):
        assert EntityResolver.resolve_priority("invalid") is None
        assert EntityResolver.resolve_priority("") is None


class TestResolveStatus:
    def test_valid_statuses(self):
        for s in VALID_STATUSES:
            assert EntityResolver.resolve_status(s) == s

    def test_aliases(self):
        assert EntityResolver.resolve_status("done") == "COMPLETED"
        assert EntityResolver.resolve_status("wip") == "IN_PROGRESS"
        assert EntityResolver.resolve_status("in progress") == "IN_PROGRESS"
        assert EntityResolver.resolve_status("to do") == "TODO"

    def test_invalid_returns_none(self):
        assert EntityResolver.resolve_status("invalid") is None


class TestResolveDate:
    def test_iso_format(self):
        result = EntityResolver.resolve_date("2026-10-10")
        assert result == date(2026, 10, 10)

    def test_today(self):
        result = EntityResolver.resolve_date("today")
        assert result == datetime.now(timezone.utc).date()

    def test_tomorrow(self):
        result = EntityResolver.resolve_date("tomorrow")
        expected = datetime.now(timezone.utc).date() + timedelta(days=1)
        assert result == expected

    def test_day_name(self):
        result = EntityResolver.resolve_date("friday")
        assert result is not None
        assert result.weekday() == 4  # Friday
        assert result > datetime.now(timezone.utc).date()  # Future

    def test_in_n_days(self):
        result = EntityResolver.resolve_date("in 3 days")
        expected = datetime.now(timezone.utc).date() + timedelta(days=3)
        assert result == expected

    def test_end_of_week(self):
        result = EntityResolver.resolve_date("end of week")
        assert result is not None
        assert result.weekday() == 4  # Friday

    def test_invalid_returns_none(self):
        assert EntityResolver.resolve_date("") is None
        assert EntityResolver.resolve_date("not a date") is None


class TestResolveProject:
    @pytest.fixture
    def resolver(self):
        task_service = AsyncMock()
        project_service = AsyncMock()
        client_service = AsyncMock()
        return EntityResolver(task_service, project_service, client_service)

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    @pytest.mark.asyncio
    async def test_exact_match(self, resolver, mock_user):
        project = MagicMock()
        project.id = uuid.uuid4()
        project.name = "Acme Website"
        project.status = "ACTIVE"
        resolver.project_service.list_projects.return_value = ([project], 1)

        result = await resolver.resolve_project("Acme Website", mock_user)
        assert result.status == ResolutionStatus.MATCHED
        assert result.entity_id == project.id

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, resolver, mock_user):
        project = MagicMock()
        project.id = uuid.uuid4()
        project.name = "Acme Website"
        project.status = "ACTIVE"
        resolver.project_service.list_projects.return_value = ([project], 1)

        result = await resolver.resolve_project("acme website", mock_user)
        assert result.status == ResolutionStatus.MATCHED

    @pytest.mark.asyncio
    async def test_ambiguous_match(self, resolver, mock_user):
        p1 = MagicMock(id=uuid.uuid4(), name="Client Portal", status="ACTIVE")
        p2 = MagicMock(id=uuid.uuid4(), name="Client Portal V2", status="ACTIVE")
        resolver.project_service.list_projects.return_value = ([p1, p2], 2)

        result = await resolver.resolve_project("Client Portal", mock_user)
        # p1 is exact match, should be MATCHED
        assert result.status == ResolutionStatus.MATCHED
        assert result.entity_id == p1.id

    @pytest.mark.asyncio
    async def test_multiple_exact_matches_ambiguous(self, resolver, mock_user):
        p1 = MagicMock(id=uuid.uuid4(), name="Client Portal", status="ACTIVE")
        p2 = MagicMock(id=uuid.uuid4(), name="Client Portal", status="ACTIVE")
        resolver.project_service.list_projects.return_value = ([p1, p2], 2)

        result = await resolver.resolve_project("Client Portal", mock_user)
        assert result.status == ResolutionStatus.AMBIGUOUS
        assert len(result.candidates) == 2

    @pytest.mark.asyncio
    async def test_not_found(self, resolver, mock_user):
        resolver.project_service.list_projects.return_value = ([], 0)

        result = await resolver.resolve_project("NonExistent", mock_user)
        assert result.status == ResolutionStatus.NOT_FOUND


class TestResolveTask:
    @pytest.fixture
    def resolver(self):
        return EntityResolver(AsyncMock(), AsyncMock(), AsyncMock())

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    @pytest.mark.asyncio
    async def test_single_match(self, resolver, mock_user):
        task = MagicMock()
        task.id = uuid.uuid4()
        task.title = "Fix login bug"
        task.status = "TODO"
        task.priority = "HIGH"
        resolver.task_service.list_tasks.return_value = ([task], 1)

        result = await resolver.resolve_task("Fix login bug", mock_user)
        assert result.status == ResolutionStatus.MATCHED
        assert result.entity_id == task.id

    @pytest.mark.asyncio
    async def test_not_found(self, resolver, mock_user):
        resolver.task_service.list_tasks.return_value = ([], 0)

        result = await resolver.resolve_task("nonexistent", mock_user)
        assert result.status == ResolutionStatus.NOT_FOUND
