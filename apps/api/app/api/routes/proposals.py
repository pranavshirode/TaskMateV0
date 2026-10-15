"""Proposal API routes — CRUD, status transitions, document export."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.ai.providers import get_ai_provider
from app.models.user import User
from app.models.proposal import Proposal, ProposalVersion
from app.schemas.proposal import (
    AIGenerateProposalRequest,
    ProposalCreate,
    ProposalResponse,
    ProposalStatusTransition,
    ProposalUpdate,
    ProposalVersionSummary,
)
from app.services.proposal import ProposalService

router = APIRouter()


def _get_proposal_service(db: AsyncSession = Depends(get_db)) -> ProposalService:
    return ProposalService(db, get_ai_provider())


def _to_response(p: Proposal) -> ProposalResponse:
    versions = getattr(p, "versions", []) or []
    return ProposalResponse(
        id=p.id,
        project_id=p.project_id,
        analysis_id=p.analysis_id,
        user_id=p.user_id,
        title=p.title,
        client_name=p.client_name,
        executive_summary=p.executive_summary,
        line_items=p.line_items or [],
        sections=p.sections or [],
        currency=p.currency,
        subtotal=p.subtotal,
        discount_percent=p.discount_percent,
        tax_percent=p.tax_percent,
        total_amount=p.total_amount,
        valid_until=p.valid_until,
        estimated_duration_weeks=p.estimated_duration_weeks,
        status=p.status,
        version=p.version,
        notes=p.notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
        version_history=[
            ProposalVersionSummary(
                id=v.id,
                version_number=v.version_number,
                change_note=v.change_note,
                created_at=v.created_at,
            )
            for v in sorted(versions, key=lambda x: x.version_number)
        ],
    )


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    data: ProposalCreate,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Create a new proposal draft."""
    proposal = await service.create_proposal(str(current_user.id), data)
    return _to_response(proposal)


@router.get("/proposals/project/{project_id}", response_model=list[ProposalResponse])
async def list_proposals(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """List all proposals for a project."""
    proposals = await service.list_proposals(str(current_user.id), project_id)
    return [_to_response(p) for p in proposals]


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Get a single proposal with version history."""
    proposal = await service.get_proposal(str(current_user.id), proposal_id)
    return _to_response(proposal)


@router.patch("/proposals/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: str,
    data: ProposalUpdate,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Update a draft or pending-approval proposal (creates a new version)."""
    proposal = await service.update_proposal(str(current_user.id), proposal_id, data)
    return _to_response(proposal)


@router.post("/proposals/{proposal_id}/transition", response_model=ProposalResponse)
async def transition_proposal_status(
    proposal_id: str,
    data: ProposalStatusTransition,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Transition proposal status (DRAFT → PENDING_APPROVAL → SENT → ACCEPTED/REJECTED)."""
    proposal = await service.transition_status(str(current_user.id), proposal_id, data)
    return _to_response(proposal)


@router.delete("/proposals/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Delete a proposal (only DRAFT or REJECTED)."""
    await service.delete_proposal(str(current_user.id), proposal_id)


# ── AI generation ─────────────────────────────────────────────────────────────

@router.post("/proposals/ai-generate", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def ai_generate_proposal(
    data: AIGenerateProposalRequest,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """AI-assisted proposal draft generation from an approved requirements analysis."""
    proposal = await service.ai_generate_proposal(str(current_user.id), data)
    return _to_response(proposal)


# ── Document export ────────────────────────────────────────────────────────────

@router.get("/proposals/{proposal_id}/markdown")
async def download_proposal_markdown(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Download the proposal as a Markdown file."""
    proposal = await service.get_proposal(str(current_user.id), proposal_id)
    md = service.generate_markdown(proposal)
    safe_title = "".join(c for c in proposal.title if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{safe_title}_v{proposal.version}.md"
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/proposals/{proposal_id}/html")
async def get_proposal_html(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    service: ProposalService = Depends(_get_proposal_service),
):
    """Return proposal as print-ready HTML (browser can save as PDF via Ctrl+P)."""
    proposal = await service.get_proposal(str(current_user.id), proposal_id)
    html = service.generate_html(proposal)
    return Response(content=html, media_type="text/html")

