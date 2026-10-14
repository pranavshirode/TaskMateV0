"""Requirement analysis never presents invented content as analysis (audit BUG-05)."""

import json

import pytest

from app.ai.errors import AIProviderError
from app.ai.providers.base import AIResponse, BaseAIProvider, ModelInfo


class FixedProvider(BaseAIProvider):
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content, self.error = content, error

    async def generate(self, messages, **kwargs):
        if self.error:
            raise self.error
        return AIResponse(content=self.content or "")

    async def health_check(self) -> bool:
        return True

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="fixed", model="fixed", max_tokens=1)


@pytest.fixture
def provider(monkeypatch):
    def _use(p: BaseAIProvider):
        monkeypatch.setattr("app.api.deps.get_ai_provider", lambda: p)

    return _use


async def _analysis(auth_client, create_test_project, brief="Online shop with Stripe checkout."):
    project = await create_test_project(auth_client._test_user.id)
    resp = await auth_client.post(
        "/api/v1/requirements/", json={"project_id": project.id, "title": "Shop", "brief": brief}
    )
    return resp.json()["id"]


async def test_invalid_ai_json_is_reported_and_nothing_saved(auth_client, create_test_project, provider):
    analysis_id = await _analysis(auth_client, create_test_project)
    provider(FixedProvider(content="Sure! Here are your requirements: ..."))

    resp = await auth_client.post(f"/api/v1/requirements/{analysis_id}/analyze")

    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "AI_INVALID_RESPONSE"
    detail = (await auth_client.get(f"/api/v1/requirements/{analysis_id}")).json()
    assert detail["requirements"] == [] and detail["status"] == "DRAFT"


async def test_provider_outage_is_reported(auth_client, create_test_project, provider):
    analysis_id = await _analysis(auth_client, create_test_project)
    provider(FixedProvider(error=AIProviderError("down")))

    resp = await auth_client.post(f"/api/v1/requirements/{analysis_id}/analyze")

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "AI_UNAVAILABLE"


async def test_sources_are_persisted_and_unlabelled_items_are_suggestions(auth_client, create_test_project, provider):
    analysis_id = await _analysis(auth_client, create_test_project)
    provider(
        FixedProvider(
            content=json.dumps(
                {
                    "functional_requirements": [
                        {
                            "title": "Stripe Checkout",
                            "description": "Pay by card via Stripe.",
                            "source": "CLIENT_STATED",
                        },
                        {"title": "Order Export", "description": "Export orders to CSV."},
                    ],
                    "non_functional_requirements": [
                        {"title": "Fast pages", "category": "PERFORMANCE", "description": "Pages load quickly."}
                    ],
                    "clarification_questions": [{"question": "Which currencies?"}],
                }
            )
        )
    )

    resp = await auth_client.post(f"/api/v1/requirements/{analysis_id}/analyze")

    assert resp.status_code == 200
    by_title = {r["title"]: r for r in resp.json()["requirements"]}
    assert by_title["Stripe Checkout"]["source"] == "CLIENT_STATED"
    assert by_title["Order Export"]["source"] == "AI_SUGGESTED"
    assert by_title["Fast pages"]["source"] == "AI_SUGGESTED"
    # Nothing beyond what the AI returned was added.
    assert len(resp.json()["requirements"]) == 3
    assert resp.json()["assumptions"] == [] and resp.json()["risks"] == []


async def test_vague_brief_with_mock_provider_asks_instead_of_inventing(auth_client, create_test_project):
    analysis_id = await _analysis(auth_client, create_test_project, brief="hello there")

    resp = await auth_client.post(f"/api/v1/requirements/{analysis_id}/analyze")

    assert resp.status_code == 200
    assert resp.json()["requirements"] == []
    assert any(q["context_topic"] == "Scope" for q in resp.json()["questions"])
