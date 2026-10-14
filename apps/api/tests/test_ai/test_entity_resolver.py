"""EntityResolver behaviour (replaces Sprint-2 tests written for an earlier resolver API)."""

from datetime import date

import pytest

from app.ai.context.resolver import EntityResolver
from app.models.enums import TaskPriority, TaskStatus

TODAY = date(2026, 10, 14)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("today", TODAY),
        ("Tomorrow", date(2026, 10, 15)),
        ("day after tomorrow", date(2026, 10, 16)),
        ("next week", date(2026, 10, 21)),
        ("due 2026-12-01 please", date(2026, 12, 1)),
        ("2026-02-30", None),
        ("someday", None),
        (None, None),
    ],
)
def test_resolve_date(raw, expected):
    assert EntityResolver.resolve_date(raw, TODAY) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("critical", TaskPriority.URGENT),
        ("High", TaskPriority.HIGH),
        ("low", TaskPriority.LOW),
        (None, TaskPriority.MEDIUM),
    ],
)
def test_resolve_priority(raw, expected):
    assert EntityResolver.resolve_priority(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("done", TaskStatus.COMPLETED),
        ("in progress", TaskStatus.IN_PROGRESS),
        ("blocked", TaskStatus.BLOCKED),
        ("in review", TaskStatus.REVIEW),
        (None, TaskStatus.TODO),
    ],
)
def test_resolve_status(raw, expected):
    assert EntityResolver.resolve_status(raw) == expected


PROJECTS = [
    {"id": "1", "name": "Client Portal"},
    {"id": "2", "name": "Client Portal V2"},
    {"id": "3", "name": "Acme Website"},
]


def test_exact_match_beats_longer_substring():
    match, ambiguous = EntityResolver.match_item("client portal", PROJECTS)
    assert match["id"] == "1" and ambiguous == []


def test_ambiguous_substring_returns_candidates_not_a_guess():
    items = [{"id": "a", "title": "Fix login bug on iOS"}, {"id": "b", "title": "Fix login bug on Android"}]
    match, ambiguous = EntityResolver.match_item("login bug", items, key="title")
    assert match is None
    assert sorted(ambiguous) == sorted(i["title"] for i in items)


def test_fuzzy_match_and_no_match():
    assert EntityResolver.match_item("Acme Webiste", PROJECTS)[0]["id"] == "3"
    assert EntityResolver.match_item("Totally different", PROJECTS) == (None, [])
