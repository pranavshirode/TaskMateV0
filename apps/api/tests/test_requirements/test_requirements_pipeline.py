"""Integration tests for Requirements Analysis Pipeline, Q&A, and Task Creation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_requirements_analysis_full_lifecycle(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
):
    user, token = await create_test_user()
    cl = await create_test_client(user.id)
    proj = await create_test_project(user.id, cl.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a requirements analysis session
    create_resp = await client.post(
        "/api/v1/requirements/",
        headers=headers,
        json={
            "project_id": proj.id,
            "title": "E-commerce Checkout Flow",
            "brief": "We need a secure checkout process with Stripe payment integration, cart validation, and order confirmation email.",
            "desired_outcome": "Complete end-to-end checkout flow tested and deployed.",
            "constraints": "Must use Stripe API v2024 and PostgreSQL.",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    analysis = create_resp.json()
    analysis_id = analysis["id"]
    assert analysis["status"] == "DRAFT"
    assert analysis["version"] == 1

    # 2. Trigger AI analysis of the brief
    analyze_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/analyze",
        headers=headers,
    )
    assert analyze_resp.status_code == 200, analyze_resp.text
    analyzed = analyze_resp.json()
    assert analyzed["version"] == 2
    assert len(analyzed["requirements"]) >= 1
    assert len(analyzed["questions"]) >= 1
    assert analyzed["status"] in ("NEEDS_CLARIFICATION", "READY_FOR_REVIEW")

    # 3. Answer a clarification question
    question = analyzed["questions"][0]
    q_id = question["id"]
    answer_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/questions/{q_id}/answer",
        headers=headers,
        json={"answer": "Yes, we will use Stripe test keys provided in 1Password."},
    )
    assert answer_resp.status_code == 200, answer_resp.text
    assert answer_resp.json()["status"] == "RESOLVED"
    assert answer_resp.json()["answer"] == "Yes, we will use Stripe test keys provided in 1Password."

    # 4. Update a requirement
    first_req = analyzed["requirements"][0]
    req_id = first_req["id"]
    update_resp = await client.put(
        f"/api/v1/requirements/{analysis_id}/requirements/{req_id}",
        headers=headers,
        json={
            "title": "Updated Feature: Stripe Checkout",
            "priority": "HIGH",
            "status": "CONFIRMED",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Feature: Stripe Checkout"
    assert update_resp.json()["status"] == "CONFIRMED"

    # 5. Explicitly approve the requirements analysis
    approve_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/approve",
        headers=headers,
    )
    assert approve_resp.status_code == 200
    approved = approve_resp.json()
    assert approved["status"] == "APPROVED"
    assert approved["approved_at"] is not None

    # 6. Generate proposed task plan
    plan_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/generate-task-plan",
        headers=headers,
    )
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert "proposed_tasks" in plan
    assert len(plan["proposed_tasks"]) >= 1
    assert "rationale" in plan

    # 7. Approve task plan and transactionally create tasks with duplicate protection
    selected_tasks = plan["proposed_tasks"][:2]
    task_approve_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/approve-task-plan",
        headers=headers,
        json={"selected_tasks": selected_tasks},
    )
    assert task_approve_resp.status_code == 200
    task_res = task_approve_resp.json()
    assert task_res["created_tasks_count"] == len(selected_tasks)
    assert task_res["traceability_links_created"] >= 1

    # 8. Test Duplicate Protection / Idempotency: re-submitting selected tasks does not duplicate them
    task_retry_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/approve-task-plan",
        headers=headers,
        json={"selected_tasks": selected_tasks},
    )
    assert task_retry_resp.status_code == 200
    assert task_retry_resp.json()["created_tasks_count"] == len(selected_tasks)
    assert task_retry_resp.json()["traceability_links_created"] == 0  # no new links created

    # 9. Verify Bidirectional Traceability
    trace_resp = await client.get(
        f"/api/v1/requirements/{analysis_id}/traceability",
        headers=headers,
    )
    assert trace_resp.status_code == 200
    trace = trace_resp.json()
    assert trace["total_requirements"] >= 1
    assert len(trace["items"]) >= 1
    assert "overall_progress_percent" in trace


@pytest.mark.asyncio
async def test_requirements_archive_and_validation(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
):
    user, token = await create_test_user(email="archive_test@example.com")
    cl = await create_test_client(user.id)
    proj = await create_test_project(user.id, cl.id)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/requirements/",
        headers=headers,
        json={
            "project_id": proj.id,
            "title": "Temporary Analysis",
            "brief": "Brief to be archived after review.",
        },
    )
    analysis_id = create_resp.json()["id"]

    # Archive analysis
    archive_resp = await client.post(
        f"/api/v1/requirements/{analysis_id}/archive",
        headers=headers,
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["status"] == "ARCHIVED"

    # Approving archived analysis must be rejected
    approve_err = await client.post(
        f"/api/v1/requirements/{analysis_id}/approve",
        headers=headers,
    )
    assert approve_err.status_code == 422
