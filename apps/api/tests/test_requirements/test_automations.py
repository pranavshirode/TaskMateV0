"""Integration tests for Workflow Automations and Daily Project Summaries."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_daily_project_summary_and_consistency(
    client: AsyncClient,
    create_test_user,
    create_test_client,
    create_test_project,
    create_test_task,
):
    user, token = await create_test_user(email="automation_user@example.com")
    cl = await create_test_client(user.id)
    proj = await create_test_project(user.id, cl.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Create real tasks in various states
    await create_test_task(user.id, title="Database Migration", project_id=proj.id)
    await create_test_task(user.id, title="Frontend Form", project_id=proj.id)

    # 1. Generate daily project summary
    summary_resp = await client.post(
        f"/api/v1/automations/projects/{proj.id}/daily-summary",
        headers=headers,
    )
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    assert summary["project_id"] == proj.id
    assert summary["project_name"] == proj.name
    assert "summary_text" in summary
    assert "generated_at" in summary

    # 2. Sync task consistency
    sync_resp = await client.post(
        f"/api/v1/automations/projects/{proj.id}/sync-consistency",
        headers=headers,
    )
    assert sync_resp.status_code == 200
    assert sync_resp.json()["status"] == "CONSISTENT"

    # 3. Verify automation execution audit records
    exec_resp = await client.get(
        "/api/v1/automations/executions",
        headers=headers,
    )
    assert exec_resp.status_code == 200
    executions = exec_resp.json()
    assert len(executions) >= 1
    assert executions[0]["automation_type"] == "DAILY_PROJECT_SUMMARY"
    assert executions[0]["status"] == "SUCCESS"
