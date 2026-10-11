"""Client Request Management and Impact Analysis Service."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ForbiddenError, ValidationError
from app.models.enums import ClientRequestStatus, ClientRequestType
from app.models.requirements import ClientRequest
from app.repositories.client_request import ClientRequestRepository
from app.repositories.project import ProjectRepository
from app.repositories.requirements import RequirementsAnalysisRepository
from app.schemas.requirements import (
    ClientRequestCreate,
    ClientRequestImpactResponse,
)
from app.ai.providers.base import AIMessage, BaseAIProvider
from app.ai.prompts.requirements import CLIENT_REQUEST_IMPACT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClientRequestService:
    def __init__(
        self,
        db: AsyncSession,
        ai_provider: BaseAIProvider,
    ):
        self.db = db
        self.ai_provider = ai_provider
        self.repo = ClientRequestRepository(db)
        self.project_repo = ProjectRepository(db)
        self.analysis_repo = RequirementsAnalysisRepository(db)

    async def _verify_project_ownership(self, user_id: str, project_id: str) -> None:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by authenticated user")

    async def create_request(
        self, user_id: str, project_id: str, data: ClientRequestCreate
    ) -> ClientRequest:
        await self._verify_project_ownership(user_id, project_id)

        try:
            req_type = ClientRequestType(data.request_type.upper())
        except ValueError:
            req_type = ClientRequestType.NEW_FEATURE

        req = ClientRequest(
            project_id=project_id,
            user_id=user_id,
            title=data.title.strip(),
            content=data.content.strip(),
            request_type=req_type,
            status=ClientRequestStatus.SUBMITTED,
        )
        return await self.repo.create(req)

    async def list_requests(
        self, user_id: str, project_id: str
    ) -> list[ClientRequest]:
        await self._verify_project_ownership(user_id, project_id)
        return await self.repo.list_by_project(project_id, user_id)

    async def get_request(self, user_id: str, request_id: str) -> ClientRequest:
        req = await self.repo.get_by_id_and_user(request_id, user_id)
        if not req:
            raise NotFoundError("Client request not found")
        return req

    async def analyze_impact(
        self, user_id: str, request_id: str
    ) -> ClientRequestImpactResponse:
        req = await self.get_request(user_id, request_id)

        # Retrieve existing project requirements analyses
        analyses = await self.analysis_repo.list_by_project(req.project_id, user_id)
        existing_reqs_str = ""
        for a in analyses:
            for r in a.requirements:
                existing_reqs_str += f"- [{r.key}] ({r.status.value}) {r.title}: {r.description}\n"

        user_prompt = f"""Incoming Client Request:
Title: {req.title}
Message:
{req.content}

Existing Project Requirements:
{existing_reqs_str or 'No existing requirements recorded.'}

Analyze the impact of this request against the existing requirements and determine if this is a new feature, change request, bug report, or clarification. Return the structured JSON assessment.
"""

        messages = [
            AIMessage(role="system", content=CLIENT_REQUEST_IMPACT_SYSTEM_PROMPT),
            AIMessage(role="user", content=user_prompt),
        ]

        response = await self.ai_provider.generate(
            messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        try:
            parsed = json.loads(response.content)
        except Exception:
            parsed = {
                "request_type": req.request_type.value,
                "classification_explanation": "Client request analyzed via rule-based classifier.",
                "affected_requirements": [],
                "affected_tasks": [],
                "scope_change_summary": "Introduces request for developer consideration.",
                "recommended_actions": ["Review brief with client", "Confirm any additional budget or deadline impact"],
            }

        req.impact_summary = parsed
        req.status = ClientRequestStatus.IMPACT_REVIEWED
        req.updated_at = datetime.now(timezone.utc)
        await self.repo.update(req)

        return ClientRequestImpactResponse(
            request_id=req.id,
            request_type=parsed.get("request_type", req.request_type.value),
            classification_explanation=parsed.get("classification_explanation", ""),
            affected_requirements=parsed.get("affected_requirements", []),
            affected_tasks=parsed.get("affected_tasks", []),
            scope_change_summary=parsed.get("scope_change_summary", ""),
            recommended_actions=parsed.get("recommended_actions", []),
        )

    async def approve_request(self, user_id: str, request_id: str) -> ClientRequest:
        req = await self.get_request(user_id, request_id)
        req.status = ClientRequestStatus.APPROVED
        req.updated_at = datetime.now(timezone.utc)
        return await self.repo.update(req)
