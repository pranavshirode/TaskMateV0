"""Entity resolution — maps AI-extracted names to real database records.

The LLM produces human-readable names (e.g., "Acme Website").
This module resolves them to actual database IDs.

Resolution rules:
- Exact match (case-insensitive) → use it
- Single fuzzy match → use it
- Multiple matches → return ambiguous (caller must ask user)
- No match → return not_found

The resolver NEVER invents IDs or silently picks from ambiguous results.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from app.models.user import User
from app.services.client import ClientService
from app.services.project import ProjectService
from app.services.task import TaskService

logger = logging.getLogger(__name__)


class ResolutionStatus(str, Enum):
    """Result status of entity resolution."""
    MATCHED = "matched"  # Exactly one match found
    AMBIGUOUS = "ambiguous"  # Multiple matches found
    NOT_FOUND = "not_found"  # No matches found


@dataclass
class ResolutionResult:
    """Result of resolving an entity name to a database record."""
    status: ResolutionStatus
    entity_id: Optional[uuid.UUID] = None  # Set when status is MATCHED
    entity_name: Optional[str] = None  # The resolved entity's actual name
    candidates: list[dict[str, Any]] = field(default_factory=list)  # Set when AMBIGUOUS
    original_query: str = ""  # The original name from the AI


# Valid values for validation
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}
VALID_STATUSES = {"TODO", "IN_PROGRESS", "REVIEW", "COMPLETED"}

# Common aliases for priorities
PRIORITY_ALIASES: dict[str, str] = {
    "low": "LOW",
    "medium": "MEDIUM",
    "med": "MEDIUM",
    "normal": "MEDIUM",
    "high": "HIGH",
    "important": "HIGH",
    "urgent": "URGENT",
    "critical": "URGENT",
    "asap": "URGENT",
}

# Common aliases for statuses
STATUS_ALIASES: dict[str, str] = {
    "todo": "TODO",
    "to do": "TODO",
    "to-do": "TODO",
    "not started": "TODO",
    "in progress": "IN_PROGRESS",
    "in-progress": "IN_PROGRESS",
    "wip": "IN_PROGRESS",
    "working": "IN_PROGRESS",
    "started": "IN_PROGRESS",
    "review": "REVIEW",
    "in review": "REVIEW",
    "under review": "REVIEW",
    "completed": "COMPLETED",
    "done": "COMPLETED",
    "finished": "COMPLETED",
    "complete": "COMPLETED",
}


class EntityResolver:
    """Resolves AI-extracted entity names to database records.

    Uses existing services (never direct DB access) to search
    for matching entities within the authenticated user's scope.
    """

    def __init__(
        self,
        task_service: TaskService,
        project_service: ProjectService,
        client_service: ClientService,
    ):
        self.task_service = task_service
        self.project_service = project_service
        self.client_service = client_service

    async def resolve_project(
        self, name: str, user: User
    ) -> ResolutionResult:
        """Resolve a project name to a project ID."""
        projects, _ = await self.project_service.list_projects(
            user, skip=0, limit=100
        )

        # Exact match (case-insensitive)
        exact = [p for p in projects if p.name.lower() == name.lower()]
        if len(exact) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=exact[0].id,
                entity_name=exact[0].name,
                original_query=name,
            )
        if len(exact) > 1:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                candidates=[{"id": str(p.id), "name": p.name, "status": p.status} for p in exact],
                original_query=name,
            )

        # Fuzzy match (contains, case-insensitive)
        fuzzy = [p for p in projects if name.lower() in p.name.lower() or p.name.lower() in name.lower()]
        if len(fuzzy) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=fuzzy[0].id,
                entity_name=fuzzy[0].name,
                original_query=name,
            )
        if len(fuzzy) > 1:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                candidates=[{"id": str(p.id), "name": p.name, "status": p.status} for p in fuzzy],
                original_query=name,
            )

        return ResolutionResult(
            status=ResolutionStatus.NOT_FOUND,
            original_query=name,
        )

    async def resolve_task(
        self, name: str, user: User
    ) -> ResolutionResult:
        """Resolve a task name/title to a task ID."""
        # Search for tasks matching the name
        tasks, _ = await self.task_service.list_tasks(
            user, skip=0, limit=100, search=name
        )

        if not tasks:
            # Try broader search with individual words
            words = name.split()
            if len(words) > 1:
                for word in words:
                    if len(word) > 2:  # Skip very short words
                        tasks, _ = await self.task_service.list_tasks(
                            user, skip=0, limit=100, search=word
                        )
                        if tasks:
                            break

        if not tasks:
            return ResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                original_query=name,
            )

        # Exact title match
        exact = [t for t in tasks if t.title.lower() == name.lower()]
        if len(exact) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=exact[0].id,
                entity_name=exact[0].title,
                original_query=name,
            )

        # Single result from search
        if len(tasks) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=tasks[0].id,
                entity_name=tasks[0].title,
                original_query=name,
            )

        # Multiple results — ambiguous
        return ResolutionResult(
            status=ResolutionStatus.AMBIGUOUS,
            candidates=[
                {"id": str(t.id), "title": t.title, "status": t.status, "priority": t.priority}
                for t in tasks[:5]  # Limit candidates
            ],
            original_query=name,
        )

    async def resolve_client(
        self, name: str, user: User
    ) -> ResolutionResult:
        """Resolve a client name to a client ID."""
        clients, _ = await self.client_service.list_clients(
            user, skip=0, limit=100
        )

        # Exact match (case-insensitive) by name or company_name
        exact = [
            c for c in clients
            if c.name.lower() == name.lower()
            or (c.company_name and c.company_name.lower() == name.lower())
        ]
        if len(exact) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=exact[0].id,
                entity_name=exact[0].name,
                original_query=name,
            )
        if len(exact) > 1:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                candidates=[{"id": str(c.id), "name": c.name, "company": c.company_name} for c in exact],
                original_query=name,
            )

        # Fuzzy match
        fuzzy = [
            c for c in clients
            if name.lower() in c.name.lower()
            or c.name.lower() in name.lower()
            or (c.company_name and (
                name.lower() in c.company_name.lower()
                or c.company_name.lower() in name.lower()
            ))
        ]
        if len(fuzzy) == 1:
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                entity_id=fuzzy[0].id,
                entity_name=fuzzy[0].name,
                original_query=name,
            )
        if len(fuzzy) > 1:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                candidates=[{"id": str(c.id), "name": c.name, "company": c.company_name} for c in fuzzy],
                original_query=name,
            )

        return ResolutionResult(
            status=ResolutionStatus.NOT_FOUND,
            original_query=name,
        )

    @staticmethod
    def resolve_priority(value: str) -> Optional[str]:
        """Resolve a priority string to a valid priority value.

        Handles aliases like 'urgent', 'critical', 'important'.
        Returns None if the value is not recognized.
        """
        normalized = value.strip().upper()
        if normalized in VALID_PRIORITIES:
            return normalized

        alias = PRIORITY_ALIASES.get(value.strip().lower())
        if alias:
            return alias

        return None

    @staticmethod
    def resolve_status(value: str) -> Optional[str]:
        """Resolve a status string to a valid status value.

        Handles aliases like 'wip', 'done', 'in progress'.
        Returns None if the value is not recognized.
        """
        normalized = value.strip().upper().replace(" ", "_")
        if normalized in VALID_STATUSES:
            return normalized

        alias = STATUS_ALIASES.get(value.strip().lower())
        if alias:
            return alias

        return None

    @staticmethod
    def resolve_date(expression: str) -> Optional[date]:
        """Resolve a date expression to an actual date.

        Supports:
        - ISO format: '2026-10-10'
        - Relative: 'today', 'tomorrow', 'yesterday'
        - Day names: 'Monday', 'Friday' (next occurrence)
        - Relative weeks: 'next week', 'end of week'
        """
        if not expression:
            return None

        expression = expression.strip().lower()
        today = datetime.now(timezone.utc).date()

        # ISO format
        try:
            return date.fromisoformat(expression)
        except ValueError:
            pass

        # Relative dates
        relative_map = {
            "today": today,
            "tomorrow": today + timedelta(days=1),
            "yesterday": today - timedelta(days=1),
            "day after tomorrow": today + timedelta(days=2),
        }
        if expression in relative_map:
            return relative_map[expression]

        # "next week" = next Monday
        if expression in ("next week", "next monday"):
            days_ahead = 7 - today.weekday()  # Monday = 0
            return today + timedelta(days=days_ahead)

        # "end of week" = Friday
        if expression in ("end of week", "end of the week", "eow"):
            days_ahead = 4 - today.weekday()  # Friday = 4
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        # Day names (next occurrence)
        day_names = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        }
        for day_name, day_num in day_names.items():
            if expression == day_name or expression == f"next {day_name}":
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        # "in X days"
        if expression.startswith("in ") and expression.endswith(" days"):
            try:
                num_days = int(expression.replace("in ", "").replace(" days", ""))
                return today + timedelta(days=num_days)
            except ValueError:
                pass

        logger.warning("Could not resolve date expression: %s", expression)
        return None
