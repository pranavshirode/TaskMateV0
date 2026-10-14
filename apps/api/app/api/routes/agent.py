"""Agent API routes for multi-step AI execution, approvals and execution traces."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.agent.orchestrator import AgentOrchestrator
from app.api.deps import get_agent_orchestrator, get_current_user
from app.core.errors import NotFoundError
from app.models.user import User

router = APIRouter()


class AgentRunRequest(BaseModel):
    prompt: str
    conversation_id: uuid.UUID | None = None


class PendingAction(BaseModel):
    step_id: str
    tool_name: str
    arguments: dict[str, Any]
    summary: str


class AgentRunResponse(BaseModel):
    conversation_id: str
    execution_id: str
    status: str
    message: str
    pending_action: PendingAction | None = None


class AgentDecisionResponse(BaseModel):
    conversation_id: str | None
    execution_id: str
    status: str
    message: str
    result: dict[str, Any] | None = None


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_number: int
    tool_name: str
    tool_input: dict[str, Any] | None
    status: str
    result_summary: str | None
    latency_ms: int
    error: str | None
    created_at: datetime


class AgentExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str | None
    status: str
    objective: str | None
    model: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    steps: list[AgentStepResponse]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> Any:
    """Execute a multi-step agent workflow. Write actions stop with a `pending_action` to approve."""
    return await orchestrator.run_agent(
        user=current_user,
        prompt=request.prompt,
        conversation_id=request.conversation_id,
    )


@router.get("/executions/{execution_id}", response_model=AgentExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> Any:
    """Execution trace: status, token usage and every tool step."""
    execution = await orchestrator.execution_service.get_execution(execution_id, current_user)
    if execution is None:
        raise NotFoundError("Agent execution not found")
    return execution


@router.post("/executions/{execution_id}/approve", response_model=AgentDecisionResponse)
async def approve_action(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> Any:
    """Run the action this execution is waiting on. Returns 409 if it was already handled."""
    return await orchestrator.resolve_pending(current_user, execution_id, approve=True)


@router.post("/executions/{execution_id}/reject", response_model=AgentDecisionResponse)
async def reject_action(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> Any:
    """Cancel the pending action without running it."""
    return await orchestrator.resolve_pending(current_user, execution_id, approve=False)
