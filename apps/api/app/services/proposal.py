"""Proposal service — CRUD, versioning, status transitions, and document generation."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.providers.base import AIMessage, BaseAIProvider
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.proposal import Proposal, ProposalVersion
from app.repositories.project import ProjectRepository
from app.schemas.proposal import (
    AIGenerateProposalRequest,
    LineItem,
    ProposalCreate,
    ProposalSection,
    ProposalStatusTransition,
    ProposalUpdate,
)

logger = logging.getLogger(__name__)

# Valid status machine transitions
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"PENDING_APPROVAL", "SENT"},
    "PENDING_APPROVAL": {"DRAFT", "SENT", "REJECTED"},
    "SENT": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": set(),  # terminal
    "REJECTED": {"DRAFT"},  # can revise and restart
}


def _compute_totals(line_items: list[Any], discount_percent: float, tax_percent: float) -> dict[str, float]:
    subtotal = sum(
        (item.get("total") or item.get("quantity", 1) * item.get("unit_price", 0))
        if isinstance(item, dict)
        else (item.total or item.quantity * item.unit_price)
        for item in line_items
    )
    discount_amount = subtotal * discount_percent / 100
    taxable = subtotal - discount_amount
    tax_amount = taxable * tax_percent / 100
    total = taxable + tax_amount
    return {
        "subtotal": round(subtotal, 2),
        "total_amount": round(total, 2),
    }


def _serialise_proposal(p: Proposal) -> dict[str, Any]:
    """Convert a Proposal ORM row to a plain dict for versioning snapshots."""
    return {
        "id": p.id,
        "project_id": p.project_id,
        "analysis_id": p.analysis_id,
        "title": p.title,
        "client_name": p.client_name,
        "executive_summary": p.executive_summary,
        "line_items": p.line_items or [],
        "sections": p.sections or [],
        "currency": p.currency,
        "subtotal": p.subtotal,
        "discount_percent": p.discount_percent,
        "tax_percent": p.tax_percent,
        "total_amount": p.total_amount,
        "valid_until": p.valid_until,
        "estimated_duration_weeks": p.estimated_duration_weeks,
        "status": p.status,
        "version": p.version,
        "notes": p.notes,
    }


class ProposalService:
    """Business logic for proposals and quotations."""

    def __init__(self, db: AsyncSession, ai_provider: BaseAIProvider | None = None) -> None:
        self.db = db
        self.ai_provider = ai_provider
        self.project_repo = ProjectRepository(db)

    async def _verify_project_owner(self, user_id: str, project_id: str) -> Any:
        project = await self.project_repo.get_by_id(project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenError("Project not found or not owned by you")
        return project

    async def _get_proposal(self, proposal_id: str, user_id: str, *, load_versions: bool = False) -> Proposal:
        stmt = select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user_id)
        if load_versions:
            stmt = stmt.options(selectinload(Proposal.versions))
        result = await self.db.execute(stmt)
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise NotFoundError("Proposal not found")
        return proposal

    async def create_proposal(self, user_id: str, data: ProposalCreate) -> Proposal:
        await self._verify_project_owner(user_id, data.project_id)

        items = [item.model_dump() for item in data.line_items]
        totals = _compute_totals(items, data.discount_percent, data.tax_percent)

        proposal = Proposal(
            project_id=data.project_id,
            analysis_id=data.analysis_id,
            user_id=user_id,
            title=data.title.strip(),
            client_name=data.client_name,
            executive_summary=data.executive_summary,
            line_items=items,
            sections=[s.model_dump() for s in data.sections],
            currency=data.currency,
            discount_percent=data.discount_percent,
            tax_percent=data.tax_percent,
            valid_until=data.valid_until,
            estimated_duration_weeks=data.estimated_duration_weeks,
            notes=data.notes,
            status="DRAFT",
            version=1,
            **totals,
        )
        self.db.add(proposal)
        await self.db.flush()  # get ID

        # Create initial version snapshot
        v = ProposalVersion(
            proposal_id=proposal.id,
            version_number=1,
            snapshot=_serialise_proposal(proposal),
            change_note="Initial draft",
        )
        self.db.add(v)
        await self.db.commit()
        return await self._get_proposal(proposal.id, user_id, load_versions=True)

    async def list_proposals(self, user_id: str, project_id: str) -> list[Proposal]:
        await self._verify_project_owner(user_id, project_id)
        stmt = (
            select(Proposal)
            .where(Proposal.project_id == project_id, Proposal.user_id == user_id)
            .options(selectinload(Proposal.versions))
            .order_by(Proposal.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_proposal(self, user_id: str, proposal_id: str) -> Proposal:
        return await self._get_proposal(proposal_id, user_id, load_versions=True)

    async def update_proposal(self, user_id: str, proposal_id: str, data: ProposalUpdate) -> Proposal:
        proposal = await self._get_proposal(proposal_id, user_id)

        if proposal.status not in ("DRAFT", "PENDING_APPROVAL"):
            raise ConflictError(
                f"Cannot edit a proposal with status '{proposal.status}'. "
                "Duplicate it or transition back to DRAFT first.",
                code="PROPOSAL_NOT_EDITABLE",
            )

        if data.title is not None:
            proposal.title = data.title.strip()
        if data.client_name is not None:
            proposal.client_name = data.client_name
        if data.executive_summary is not None:
            proposal.executive_summary = data.executive_summary
        if data.line_items is not None:
            proposal.line_items = [i.model_dump() for i in data.line_items]
        if data.sections is not None:
            proposal.sections = [s.model_dump() for s in data.sections]
        if data.currency is not None:
            proposal.currency = data.currency
        if data.discount_percent is not None:
            proposal.discount_percent = data.discount_percent
        if data.tax_percent is not None:
            proposal.tax_percent = data.tax_percent
        if data.valid_until is not None:
            proposal.valid_until = data.valid_until
        if data.estimated_duration_weeks is not None:
            proposal.estimated_duration_weeks = data.estimated_duration_weeks
        if data.notes is not None:
            proposal.notes = data.notes
        if data.status is not None:
            # status transitions handled by transition_status; only allow here within editable states
            if data.status not in _ALLOWED_TRANSITIONS.get(proposal.status, set()):
                raise ValidationError(
                    f"Cannot transition from '{proposal.status}' to '{data.status}'. "
                    "Use the /transition endpoint."
                )
            proposal.status = data.status

        # Recompute totals
        totals = _compute_totals(proposal.line_items or [], proposal.discount_percent, proposal.tax_percent)
        proposal.subtotal = totals["subtotal"]
        proposal.total_amount = totals["total_amount"]
        proposal.version += 1
        proposal.updated_at = datetime.now(timezone.utc)

        # Snapshot new version
        v = ProposalVersion(
            proposal_id=proposal.id,
            version_number=proposal.version,
            snapshot=_serialise_proposal(proposal),
            change_note=f"Updated to version {proposal.version}",
        )
        self.db.add(v)
        await self.db.commit()
        await self.db.refresh(proposal, attribute_names=["versions"])
        return await self._get_proposal(proposal_id, user_id, load_versions=True)

    async def transition_status(
        self, user_id: str, proposal_id: str, data: ProposalStatusTransition
    ) -> Proposal:
        proposal = await self._get_proposal(proposal_id, user_id, load_versions=True)
        allowed = _ALLOWED_TRANSITIONS.get(proposal.status, set())
        if data.status not in allowed:
            raise ConflictError(
                f"Cannot transition proposal from '{proposal.status}' to '{data.status}'. "
                f"Allowed transitions: {', '.join(allowed) or 'none'}.",
                code="INVALID_STATUS_TRANSITION",
            )
        proposal.status = data.status
        proposal.updated_at = datetime.now(timezone.utc)
        if data.note:
            proposal.notes = (proposal.notes or "") + f"\n[{data.status}] {data.note}"

        await self.db.commit()
        return proposal

    async def delete_proposal(self, user_id: str, proposal_id: str) -> None:
        proposal = await self._get_proposal(proposal_id, user_id)
        if proposal.status in ("ACCEPTED", "SENT"):
            raise ConflictError(
                f"Cannot delete a proposal with status '{proposal.status}'.",
                code="PROPOSAL_NOT_DELETABLE",
            )
        await self.db.delete(proposal)
        await self.db.commit()

    # ── Document Generation ────────────────────────────────────────────────────

    def generate_markdown(self, proposal: Proposal) -> str:
        """Render proposal as Markdown for download or HTML conversion."""
        lines: list[str] = []

        lines += [
            f"# {proposal.title}",
            f"",
            f"**Status:** {proposal.status}  |  **Version:** {proposal.version}  |  "
            f"**Currency:** {proposal.currency}",
            f"",
        ]

        if proposal.client_name:
            lines += [f"**Prepared for:** {proposal.client_name}", ""]

        if proposal.valid_until:
            lines += [f"**Valid Until:** {proposal.valid_until}", ""]

        if proposal.estimated_duration_weeks:
            lines += [f"**Estimated Duration:** {proposal.estimated_duration_weeks} weeks", ""]

        lines += ["---", ""]

        if proposal.executive_summary:
            lines += ["## Executive Summary", "", proposal.executive_summary, ""]

        # Custom sections
        for section in proposal.sections or []:
            if isinstance(section, dict):
                heading = section.get("heading", "")
                content = section.get("content", "")
            else:
                heading = section.heading
                content = section.content
            lines += [f"## {heading}", "", content, ""]

        # Pricing table
        if proposal.line_items:
            lines += [
                "## Pricing",
                "",
                "| # | Description | Qty | Unit Price | Total |",
                "|---|---|---|---|---|",
            ]
            for i, item in enumerate(proposal.line_items, 1):
                if isinstance(item, dict):
                    desc = item.get("description", "")
                    qty = item.get("quantity", 1)
                    unit = item.get("unit_price", 0)
                    total = item.get("total") or qty * unit
                else:
                    desc, qty, unit, total = item.description, item.quantity, item.unit_price, item.total or 0
                lines.append(f"| {i} | {desc} | {qty} | {unit:.2f} | {total:.2f} |")

            lines += [
                "",
                f"**Subtotal:** {proposal.subtotal or 0:.2f} {proposal.currency}",
            ]
            if proposal.discount_percent:
                lines.append(f"**Discount:** {proposal.discount_percent:.1f}%")
            if proposal.tax_percent:
                lines.append(f"**Tax:** {proposal.tax_percent:.1f}%")
            lines += [
                f"**Total:** {proposal.total_amount or 0:.2f} {proposal.currency}",
                "",
            ]

        if proposal.notes:
            lines += ["## Notes", "", proposal.notes, ""]

        lines += [
            "---",
            f"_Generated by TaskMate AI on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        ]

        return "\n".join(lines)

    def generate_html(self, proposal: Proposal) -> str:
        """Render a print-ready HTML proposal (browser prints to PDF)."""
        md = self.generate_markdown(proposal)
        # Simple Markdown → HTML conversion for the most common elements
        import re

        html_lines: list[str] = []
        for line in md.split("\n"):
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("| "):
                # Table row
                cells = [c.strip() for c in line.strip("|").split("|")]
                tag = "th" if "---" not in line else None
                if tag is None:
                    continue  # skip separator row
                html_lines.append(
                    "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
                )
            elif line.startswith("---"):
                html_lines.append("<hr>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<p><strong>{line.strip('*')}</strong></p>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "":
                html_lines.append("<br>")
            else:
                # Inline bold
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                html_lines.append(f"<p>{line}</p>")

        body = "\n".join(html_lines)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{proposal.title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto; color: #1a1a1a; }}
  h1 {{ color: #0f172a; border-bottom: 2px solid #6366f1; padding-bottom: 8px; }}
  h2 {{ color: #334155; margin-top: 2em; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
  th {{ background: #f8fafc; font-weight: 600; }}
  hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2em 0; }}
  @media print {{
    body {{ margin: 20px; }}
    @page {{ margin: 2cm; }}
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""

    # ── AI-Assisted Generation ─────────────────────────────────────────────────

    async def ai_generate_proposal(
        self, user_id: str, data: AIGenerateProposalRequest
    ) -> Proposal:
        """Use AI to draft a proposal from an approved requirements analysis."""
        if self.ai_provider is None:
            raise ConflictError("AI provider not configured.", code="AI_UNAVAILABLE")

        project = await self._verify_project_owner(user_id, data.project_id)

        # Fetch the analysis to get requirements summary
        from sqlalchemy import text as sql_text

        stmt = sql_text(
            "SELECT title, brief, status FROM requirements_analyses WHERE id = :id AND user_id = :uid"
        )
        res = await self.db.execute(stmt, {"id": data.analysis_id, "uid": user_id})
        row = res.first()
        if not row:
            raise NotFoundError("Requirements analysis not found")

        analysis_title, brief, analysis_status = row

        prompt = f"""You are helping a freelance developer create a client proposal.

Project: {project.name}
Analysis Title: {analysis_title}
Client Brief: {brief}
Additional Notes: {data.additional_notes or "None"}

Generate a structured project proposal with these JSON fields:
{{
  "title": "...",
  "client_name": null,
  "executive_summary": "2-3 paragraphs summarising the project and your approach",
  "sections": [
    {{"heading": "Project Scope", "content": "..."}},
    {{"heading": "Deliverables", "content": "..."}},
    {{"heading": "Timeline", "content": "..."}},
    {{"heading": "Terms & Conditions", "content": "..."}}
  ],
  "line_items": [
    {{"description": "...", "quantity": 1, "unit_price": 0}},
    ...
  ],
  "estimated_duration_weeks": 4,
  "valid_until": "2026-12-31",
  "notes": "..."
}}

Base pricing on the complexity described in the brief. Do not fabricate numbers — use round estimates.
Respond with ONLY valid JSON."""

        try:
            response = await self.ai_provider.generate(
                [AIMessage(role="user", content=prompt)],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2048,
            )
            parsed = json.loads(response.content)
        except Exception as e:
            logger.warning("AI proposal generation failed: %s", e)
            raise ConflictError(
                "AI could not generate a proposal. Please create one manually.",
                code="AI_GENERATION_FAILED",
            ) from e

        line_items = [
            LineItem(
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
            )
            for item in parsed.get("line_items", [])
        ]
        sections = [
            ProposalSection(heading=s.get("heading", ""), content=s.get("content", ""))
            for s in parsed.get("sections", [])
        ]

        create_data = ProposalCreate(
            project_id=data.project_id,
            analysis_id=data.analysis_id,
            title=parsed.get("title", f"Proposal: {analysis_title}"),
            client_name=parsed.get("client_name"),
            executive_summary=parsed.get("executive_summary"),
            line_items=line_items,
            sections=sections,
            estimated_duration_weeks=parsed.get("estimated_duration_weeks"),
            valid_until=parsed.get("valid_until"),
            notes=parsed.get("notes"),
        )
        return await self.create_proposal(user_id, create_data)

