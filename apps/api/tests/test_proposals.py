"""Tests for proposals — CRUD, status transitions, and document export."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProposals:
    async def _create_proposal(self, auth_client: AsyncClient, project_id: str) -> dict:
        resp = await auth_client.post(
            "/api/v1/proposals",
            json={
                "project_id": project_id,
                "title": "Test Proposal",
                "executive_summary": "We will build a great product.",
                "line_items": [
                    {"description": "Backend development", "quantity": 1, "unit_price": 3000},
                    {"description": "Frontend development", "quantity": 1, "unit_price": 2000},
                ],
                "currency": "USD",
                "discount_percent": 5.0,
                "tax_percent": 18.0,
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_create_proposal(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        data = await self._create_proposal(auth_client, project.id)
        assert data["title"] == "Test Proposal"
        assert data["status"] == "DRAFT"
        assert data["version"] == 1
        assert data["subtotal"] == 5000.0
        # total = (5000 * 0.95) * 1.18 = 4750 * 1.18 = 5605
        assert data["total_amount"] == pytest.approx(5605.0, abs=1.0)
        assert len(data["version_history"]) == 1

    async def test_list_proposals(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        await self._create_proposal(auth_client, project.id)
        resp = await auth_client.get(f"/api/v1/proposals/project/{project.id}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1

    async def test_get_proposal(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        resp = await auth_client.get(f"/api/v1/proposals/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_update_proposal(self, auth_client: AsyncClient, create_test_project):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]

        resp = await auth_client.patch(
            f"/api/v1/proposals/{pid}",
            json={"title": "Updated Proposal", "notes": "Added notes"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Proposal"
        assert data["version"] == 2
        assert len(data["version_history"]) == 2

    async def test_status_transition_draft_to_sent(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]

        resp = await auth_client.post(
            f"/api/v1/proposals/{pid}/transition",
            json={"status": "SENT", "note": "Sent to client"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SENT"

    async def test_invalid_status_transition(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]
        # DRAFT → ACCEPTED is not allowed (must go through SENT first)
        resp = await auth_client.post(
            f"/api/v1/proposals/{pid}/transition",
            json={"status": "ACCEPTED"},
        )
        assert resp.status_code == 409

    async def test_delete_draft_proposal(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]

        resp = await auth_client.delete(f"/api/v1/proposals/{pid}")
        assert resp.status_code == 204

    async def test_cannot_delete_sent_proposal(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]
        await auth_client.post(
            f"/api/v1/proposals/{pid}/transition",
            json={"status": "SENT"},
        )
        resp = await auth_client.delete(f"/api/v1/proposals/{pid}")
        assert resp.status_code == 409

    async def test_download_markdown(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]
        resp = await auth_client.get(f"/api/v1/proposals/{pid}/markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "Test Proposal" in resp.text

    async def test_get_html(
        self, auth_client: AsyncClient, create_test_project
    ):
        user_id = auth_client._test_user.id
        project = await create_test_project(user_id)
        created = await self._create_proposal(auth_client, project.id)
        pid = created["id"]
        resp = await auth_client.get(f"/api/v1/proposals/{pid}/html")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Test Proposal" in resp.text

    async def test_wrong_project_forbidden(
        self, auth_client: AsyncClient
    ):
        resp = await auth_client.post(
            "/api/v1/proposals",
            json={"project_id": "nonexistent", "title": "Bad"},
        )
        assert resp.status_code in (403, 404)
