"""Agent API routes for multi-step AI execution."""

import uuid
from typing import Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_agent_orchestrator
from app.models.user import User
from app.agent.orchestrator import AgentOrchestrator


router = APIRouter()


class AgentRunRequest(BaseModel):
    prompt: str
    conversation_id: Optional[uuid.UUID] = None


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

