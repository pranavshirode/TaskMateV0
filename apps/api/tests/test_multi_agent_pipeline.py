"""Tests for the Multi-Agent Orchestration Pipeline."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pipeline_end_to_end_success(
    auth_client: AsyncClient, create_test_project
):
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id, name="FinTech Portal")

    brief = (
        "We need a secure customer portal by December 2026 where users can register, view account balances, "
        "download monthly statements as PDF, and initiate payments using Stripe with 2FA verification. "
        "The backend must be built in Python with PostgreSQL, and all transactions must be audit logged."
    )

    resp = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": project.id,
            "brief": brief,
            "title": "Customer Portal Requirements",
            "auto_approve_requirements": True,
            "auto_create_tasks": True,
            "auto_create_proposal": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
    assert data["project_id"] == project.id
    assert data["requirements_count"] > 0
    assert data["planned_tasks_count"] > 0
    assert data["proposal_id"] is not None

    stage_names = [s["stage_name"] for s in data["stages"]]
    assert "Requirement Analyzer" in stage_names
    assert "Task Planner" in stage_names
    assert "Proposal Generator" in stage_names


@pytest.mark.asyncio
async def test_pipeline_pauses_for_clarification(
    auth_client: AsyncClient, create_test_project
):
    """When a brief has essential unknowns, the pipeline must pause for clarification."""
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id, name="Ambiguous App")

    # A short, vague brief that triggers clarification questions
    brief = "Build an app for my company."

    resp = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": project.id,
            "brief": brief,
            "title": "Vague App Spec",
            "auto_approve_requirements": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CLARIFICATION_REQUIRED"
    assert data["unresolved_questions_count"] > 0

    stages = {s["stage_name"]: s for s in data["stages"]}
    assert stages["Requirement Analyzer"]["status"] == "PAUSED_FOR_CLARIFICATION"
    assert stages["Task Planner"]["status"] == "SKIPPED"
    assert stages["Proposal Generator"]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_pipeline_resume_after_answering_clarifications(
    auth_client: AsyncClient, create_test_project
):
    """Pipeline can pause on questions, allow developer to answer, and resume to completion."""
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id, name="Healthcare Clinic Portal")

    brief = "Build a patient appointment booking app with email reminders."

    exec_resp = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": project.id,
            "brief": brief,
            "title": "Clinic Portal Spec",
        },
    )
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] == "CLARIFICATION_REQUIRED"
    analysis_id = data["analysis_id"]

    # Fetch questions
    detail_resp = await auth_client.get(f"/api/v1/requirements/{analysis_id}")
    assert detail_resp.status_code == 200
    questions = detail_resp.json()["questions"]
    assert len(questions) > 0

    # Answer all questions
    for q in questions:
        ans_resp = await auth_client.post(
            f"/api/v1/requirements/{analysis_id}/questions/{q['id']}/answer",
            json={"answer": "We are targeting launch by December 2026 for both iOS and Android with automated reminders."},
        )
        assert ans_resp.status_code == 200

    # Resume pipeline
    resume_resp = await auth_client.post(
        "/api/v1/requirements/pipeline/resume",
        json={
            "analysis_id": analysis_id,
            "auto_approve_requirements": True,
            "auto_create_tasks": True,
            "auto_create_proposal": True,
        },
    )
    assert resume_resp.status_code == 200
    resumed_data = resume_resp.json()
    assert resumed_data["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
    assert resumed_data["proposal_id"] is not None


@pytest.mark.asyncio
async def test_pipeline_approval_gating(
    auth_client: AsyncClient, create_test_project
):
    """When requirements are ready but not yet approved, downstream actions wait for developer review."""
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id, name="E-Commerce Store")

    brief = (
        "Build an e-commerce catalog by December 2026 with search, cart, Stripe checkout, "
        "and user account management using Next.js and FastAPI."
    )

    resp = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": project.id,
            "brief": brief,
            "auto_approve_requirements": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "PENDING_REQUIREMENT_APPROVAL"
    stages = {s["stage_name"]: s for s in data["stages"]}
    assert stages["Requirement Analyzer"]["status"] == "COMPLETED"
    assert stages["Task Planner"]["status"] == "AWAITING_APPROVAL"


@pytest.mark.asyncio
async def test_pipeline_duplicate_prevention_on_retry(
    auth_client: AsyncClient, create_test_project
):
    """Re-executing or resuming the pipeline must not create duplicate proposal records."""
    user_id = auth_client._test_user.id
    project = await create_test_project(user_id, name="SaaS Platform")

    brief = (
        "Build a SaaS monitoring dashboard by December 2026 with uptime checks, alert webhooks, "
        "and team member invite links."
    )

    # First run
    resp1 = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": project.id,
            "brief": brief,
            "auto_approve_requirements": True,
            "auto_create_proposal": True,
        },
    )
    assert resp1.status_code == 200
    prop_id_1 = resp1.json().get("proposal_id")
    analysis_id = resp1.json()["analysis_id"]

    if prop_id_1:
        # Resume / retry on the same analysis
        resp2 = await auth_client.post(
            "/api/v1/requirements/pipeline/resume",
            json={
                "analysis_id": analysis_id,
                "auto_approve_requirements": True,
                "auto_create_proposal": True,
            },
        )
        assert resp2.status_code == 200
        prop_id_2 = resp2.json().get("proposal_id")
        assert prop_id_1 == prop_id_2, "Pipeline must reuse existing proposal without creating duplicates"


@pytest.mark.asyncio
async def test_pipeline_unauthorized_access(auth_client: AsyncClient):
    """Accessing an invalid or unauthorized project must fail."""
    resp = await auth_client.post(
        "/api/v1/requirements/pipeline/execute",
        json={
            "project_id": "nonexistent-project-uuid",
            "brief": "Valid brief content with sufficient length.",
        },
    )
    assert resp.status_code in (403, 404)

