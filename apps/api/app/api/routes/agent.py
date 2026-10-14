"""Agent API routes for multi-step AI execution."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agent.orchestrator import AgentOrchestrator
from app.api.deps import get_agent_orchestrator, get_current_user
from app.models.user import User

router = APIRouter()


class AgentRunRequest(BaseModel):
    prompt: str
    conversation_id: uuid.UUID | None = None


class AgentRunResponse(BaseModel):
    conversation_id: str
    execution_id: str
    status: str
    message: str


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> Any:
    """Execute a multi-step agent workflow."""
    result = await orchestrator.run_agent(
        user=current_user,
        prompt=request.prompt,
        conversation_id=request.conversation_id,
    )
    return result
