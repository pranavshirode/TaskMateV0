"""Service layer for agent execution management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.agent_execution import AgentExecution, AgentExecutionStep
from app.models.user import User
from app.repositories.agent_execution import AgentExecutionRepository


class AgentExecutionService:
    """Business logic for agent execution tracking."""

    def __init__(self, repository: AgentExecutionRepository):
        self.repository = repository

    async def create_execution(
        self,
        user: User,
        conversation_id: str | uuid.UUID | None = None,
        objective: str | None = None,
        model: str | None = None,
    ) -> AgentExecution:
        return await self.repository.create_execution(
            user_id=str(user.id),
            conversation_id=str(conversation_id) if conversation_id else None,
            objective=objective,
            model=model,
        )

    async def start_execution(self, execution: AgentExecution) -> AgentExecution:
        return await self.repository.update_execution(
            execution, status="RUNNING", started_at=datetime.now(timezone.utc)
        )

    async def complete_execution(self, execution: AgentExecution, **token_kwargs: Any) -> AgentExecution:
        return await self.repository.update_execution(
            execution,
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc),
            **token_kwargs,
        )

    async def fail_execution(self, execution: AgentExecution, error: str) -> AgentExecution:
        return await self.repository.update_execution(
            execution,
            status="FAILED",
            error=error,
            completed_at=datetime.now(timezone.utc),
        )

    async def timeout_execution(self, execution: AgentExecution) -> AgentExecution:
        return await self.repository.update_execution(
            execution,
            status="TIMEOUT",
            completed_at=datetime.now(timezone.utc),
            error="Execution time limit exceeded",
        )

    async def update_execution(self, execution: AgentExecution, **fields: Any) -> AgentExecution:
        return await self.repository.update_execution(execution, **fields)

    async def complete_step(
        self, step: AgentExecutionStep, result_summary: str, latency_ms: int = 0
    ) -> AgentExecutionStep:
        return await self.repository.update_step(
            step, status="COMPLETED", result_summary=result_summary, latency_ms=latency_ms
        )

    async def update_step(self, step: AgentExecutionStep, **fields: Any) -> AgentExecutionStep:
        return await self.repository.update_step(step, **fields)

    async def fail_step(self, step: AgentExecutionStep, error: str, latency_ms: int = 0) -> AgentExecutionStep:
        return await self.repository.update_step(step, status="FAILED", error=error, latency_ms=latency_ms)

    async def transition_status(self, execution_id: str, user: User, from_status: str, to_status: str) -> bool:
        return await self.repository.transition_status(str(execution_id), str(user.id), from_status, to_status)

    async def get_execution(self, execution_id: str | uuid.UUID, user: User) -> AgentExecution | None:
        return await self.repository.get_execution(str(execution_id), str(user.id))

    async def cancel_execution(self, execution: AgentExecution) -> AgentExecution:
        return await self.repository.update_execution(
            execution,
            status="CANCELLED",
            completed_at=datetime.now(timezone.utc),
            error="Execution was cancelled",
        )

    async def record_step(
        self,
        execution: AgentExecution,
        step_number: int,
        tool_name: str,
        tool_input: dict[str, Any] | None = None,
        status: str = "PENDING",
        result_summary: str | None = None,
        latency_ms: int = 0,
        error: str | None = None,
    ) -> AgentExecutionStep:
        return await self.repository.add_step(
            execution_id=execution.id,
            step_number=step_number,
            tool_name=tool_name,
            tool_input=tool_input,
            status=status,
            result_summary=result_summary,
            latency_ms=latency_ms,
            error=error,
        )
