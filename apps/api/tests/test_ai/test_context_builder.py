"""Tests for context builder."""
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.ai.context.builder import ContextBuilder


class TestContextBuilder:
    @pytest.fixture
    def mock_services(self):
        return {
            "task_service": AsyncMock(),
            "project_service": AsyncMock(),
            "client_service": AsyncMock(),
            "dashboard_service": AsyncMock(),
        }

    @pytest.fixture
    def builder(self, mock_services):
        return ContextBuilder(**mock_services)

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid.uuid4()
        user.full_name = "Test User"
        return user

    @pytest.mark.asyncio
    async def test_build_context_empty(self, builder, mock_user, mock_services):
        mock_services["project_service"].list_projects.return_value = ([], 0)
        mock_services["client_service"].list_clients.return_value = ([], 0)
        mock_services["task_service"].list_tasks.return_value = ([], 0)
        mock_services["dashboard_service"].get_today_dashboard.return_value = {
            "date": "2026-10-05", "due_today": [], "overdue": [],
            "high_priority": [], "recently_updated": [], "active_projects": [],
        }

        context = await builder.build_context(mock_user)
        assert context.summary.task_count == 0
        assert context.summary.project_count == 0
        assert "None" in context.formatted_text

    @pytest.mark.asyncio
    async def test_build_context_with_data(self, builder, mock_user, mock_services):
        project = MagicMock(id=uuid.uuid4(), name="Acme", status="ACTIVE", client_id=None)
        task = MagicMock(id=uuid.uuid4(), title="Fix bug", status="TODO", priority="HIGH", due_date=None, project_id=None)
        client = MagicMock(id=uuid.uuid4(), name="John", company_name="Acme Inc", status="ACTIVE")

        mock_services["project_service"].list_projects.return_value = ([project], 1)
        mock_services["client_service"].list_clients.return_value = ([client], 1)
        mock_services["task_service"].list_tasks.return_value = ([task], 1)
        mock_services["dashboard_service"].get_today_dashboard.return_value = {
            "date": "2026-10-05", "due_today": [], "overdue": [],
            "high_priority": [task], "recently_updated": [], "active_projects": [project],
        }

        context = await builder.build_context(mock_user)
        assert context.summary.task_count == 1
        assert context.summary.project_count == 1
        assert "Acme" in context.formatted_text
        assert "Fix bug" in context.formatted_text

    @pytest.mark.asyncio
    async def test_service_failure_graceful(self, builder, mock_user, mock_services):
        mock_services["project_service"].list_projects.side_effect = Exception("DB error")
        mock_services["client_service"].list_clients.return_value = ([], 0)
        mock_services["task_service"].list_tasks.return_value = ([], 0)
        mock_services["dashboard_service"].get_today_dashboard.return_value = {
            "date": "2026-10-05", "due_today": [], "overdue": [],
            "high_priority": [], "recently_updated": [], "active_projects": [],
        }

        # Should not raise, just return empty projects
        context = await builder.build_context(mock_user)
        assert context.summary.project_count == 0

    def test_get_project_names(self, builder):
        context = MagicMock()
        context.projects = [{"name": "Acme"}, {"name": "Portal"}]
        result = builder.get_project_names(context)
        assert "Acme" in result
        assert "Portal" in result

    def test_get_project_names_empty(self, builder):
        context = MagicMock()
        context.projects = []
        result = builder.get_project_names(context)
        assert "No projects" in result
