"""Entity Resolution: Matches natural language entity references to real DB records."""
from __future__ import annotations

import difflib
import re
from datetime import date, timedelta
from typing import Any

from app.ai.context.builder import AIContext
from app.models.enums import TaskPriority, TaskStatus


class ResolvedEntities:
    def __init__(
        self,
        project_id: str | None = None,
        project_name: str | None = None,
        client_id: str | None = None,
        client_name: str | None = None,
        task_id: str | None = None,
        task_title: str | None = None,
        due_date: date | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        ambiguous_matches: list[str] | None = None,
    ):
        self.project_id = project_id
        self.project_name = project_name
        self.client_id = client_id
        self.client_name = client_name
        self.task_id = task_id
        self.task_title = task_title
        self.due_date = due_date
        self.status = status
        self.priority = priority
        self.ambiguous_matches = ambiguous_matches or []


class EntityResolver:
    """Resolves extracted entity strings against user workspace context."""

    @staticmethod
    def resolve_date(raw_date: str | None, current_date: date) -> date | None:
        if not raw_date:
            return None

        raw = raw_date.strip().lower()

        if raw in ["today", "by today", "end of today"]:
            return current_date
        if raw in ["tomorrow", "by tomorrow", "end of tomorrow"]:
            return current_date + timedelta(days=1)
        if raw in ["in 2 days", "after 2 days", "day after tomorrow"]:
            return current_date + timedelta(days=2)
        if raw in ["next week", "in a week", "1 week"]:
            return current_date + timedelta(days=7)

        # Try parsing ISO YYYY-MM-DD
        iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", raw)
        if iso_match:
            try:
                return date(
                    int(iso_match.group(1)),
                    int(iso_match.group(2)),
                    int(iso_match.group(3)),
                )
            except ValueError:
                pass

        return None

    @staticmethod
    def resolve_priority(raw_priority: str | None) -> TaskPriority:
        if not raw_priority:
            return TaskPriority.MEDIUM

        raw = raw_priority.strip().upper()
        if "URGENT" in raw or "CRITICAL" in raw:
            return TaskPriority.URGENT
        if "HIGH" in raw:
            return TaskPriority.HIGH
        if "LOW" in raw:
            return TaskPriority.LOW
        return TaskPriority.MEDIUM

    @staticmethod
    def resolve_status(raw_status: str | None) -> TaskStatus:
        if not raw_status:
            return TaskStatus.TODO

        raw = raw_status.strip().upper().replace(" ", "_")
        if "COMPLETE" in raw or "DONE" in raw:
            return TaskStatus.COMPLETED
        if "PROGRESS" in raw or "DOING" in raw:
            return TaskStatus.IN_PROGRESS
        if "BLOCK" in raw:
            return TaskStatus.BLOCKED
        if "REVIEW" in raw:
            return TaskStatus.REVIEW
        if "BACKLOG" in raw:
            return TaskStatus.BACKLOG
        return TaskStatus.TODO

    @staticmethod
    def match_item(query: str, items: list[dict[str, Any]], key: str = "name") -> tuple[dict[str, Any] | None, list[str]]:
        """Match query against items with exact, case-insensitive, substring, and fuzzy matching."""
        if not query or not items:
            return None, []

        q = query.strip().lower()

        # 1. Exact match
        for item in items:
            name = item.get(key, "").strip().lower()
            if name == q:
                return item, []

        # 2. Substring match
        substring_matches = [
            item for item in items if q in item.get(key, "").strip().lower() or item.get(key, "").strip().lower() in q
        ]
        if len(substring_matches) == 1:
            return substring_matches[0], []
        elif len(substring_matches) > 1:
            # Check if one is a much better match
            exact_start = [item for item in substring_matches if item.get(key, "").strip().lower().startswith(q)]
            if len(exact_start) == 1:
                return exact_start[0], []
            return None, [item.get(key, "") for item in substring_matches]

        # 3. Fuzzy matching
        names = [item.get(key, "") for item in items]
        close_matches = difflib.get_close_matches(query, names, n=3, cutoff=0.6)
        if len(close_matches) == 1:
            for item in items:
                if item.get(key, "") == close_matches[0]:
                    return item, []
        elif len(close_matches) > 1:
            return None, close_matches

        return None, []

    @classmethod
    def resolve(
        cls,
        context: AIContext,
        project_ref: str | None = None,
        client_ref: str | None = None,
        task_ref: str | None = None,
        raw_date: str | None = None,
        raw_priority: str | None = None,
        raw_status: str | None = None,
    ) -> ResolvedEntities:
        ambiguities: list[str] = []

        # Project
        matched_proj = None
        if project_ref:
            matched_proj, proj_ambig = cls.match_item(project_ref, context.projects, "name")
            if proj_ambig:
                ambiguities.extend([f"Project: {p}" for p in proj_ambig])

        # Client
        matched_client = None
        if client_ref:
            matched_client, client_ambig = cls.match_item(client_ref, context.clients, "name")
            if client_ambig:
                ambiguities.extend([f"Client: {c}" for c in client_ambig])

        # Task
        matched_task = None
        if task_ref:
            # Clean task_ref: remove words like "the", "task"
            clean_task = re.sub(r"^(the\s+)?(task\s+)?", "", task_ref.strip(), flags=re.IGNORECASE).strip()
            matched_task, task_ambig = cls.match_item(clean_task, context.recent_tasks, "title")
            if task_ambig:
                ambiguities.extend([f"Task: {t}" for t in task_ambig])

        # Date, Priority, Status
        due_date = cls.resolve_date(raw_date, context.current_date)
        priority = cls.resolve_priority(raw_priority) if raw_priority else None
        status = cls.resolve_status(raw_status) if raw_status else None

        return ResolvedEntities(
            project_id=matched_proj["id"] if matched_proj else None,
            project_name=matched_proj["name"] if matched_proj else None,
            client_id=matched_client["id"] if matched_client else None,
            client_name=matched_client["name"] if matched_client else None,
            task_id=matched_task["id"] if matched_task else None,
            task_title=matched_task["title"] if matched_task else None,
            due_date=due_date,
            status=status,
            priority=priority,
            ambiguous_matches=ambiguities,
        )

