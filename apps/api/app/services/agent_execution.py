"""Service layer for agent execution management."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from app.models.agent_execution import AgentExecution, AgentExecutionStep
from app.models.user import User
from app.repositories.agent_execution import AgentExecutionRepository


class AgentExecutionService:
    """Business logic for agent execution tracking."""

    def __init__(self, repository: AgentExecutionRepository):
        self.repository = repository

    async def create_execution(
        self, user: User, conversation_id: Optional[uuid.UUID] = None,
        objective: Optional[str] = None, model: Optional[str] = None,
    ) -> AgentExecution:
        return await self.repository.create_execution(
            user_id=user.id, conversation_id=conversation_id,
            objective=objective, model=model,
        )

    async def start_execution(self, execution: AgentExecution) -> AgentExecution:
        return await self.repository.update_execution(
            execution, status="RUNNING", started_at=datetime.now(timezone.utc)
        )

    async def complete_execution(
        self, execution: AgentExecution, **token_kwargs: Any
    ) -> AgentExecution:
        return await self.repository.update_execution(
            execution, status="COMPLETED",
            completed_at=datetime.now(timezone.utc), **token_kwargs
        )

    async def fail_execution(
        self, execution: AgentExecution, error: str
    ) -> AgentExecution:
        return await self.repository.update_execution(
            execution, status="FAILED", error=error,
            completed_at=datetime.now(timezone.utc)
        )

    async def timeout_execution(self, execution: AgentExecution) -> AgentExecution:
        return await self.repository.update_execution(
            execution, status="TIMEOUT",
            completed_at=datetime.now(timezone.utc),
            error="Execution time limit exceeded"
        )

    async def get_execution(
        self, execution_id: uuid.UUID, user: User
    ) -> Optional[AgentExecution]:
        return await self.repository.get_execution(execution_id, user.id)

    async def cancel_execution(
        self, execution_id: uuid.UUID, user: User
    ) -> Optional[AgentExecution]:
        return await self.repository.cancel_execution(execution_id, user.id)

    async def record_step(
        self, execution: AgentExecution, tool_name: str,
        tool_input: Optional[dict] = None,
    ) -> AgentExecutionStep:
        step = await self.repository.add_step(
            execution_id=execution.id,
            step_number=execution.current_step + 1,
            tool_name=tool_name,
            tool_input=tool_input,
        )
        await self.repository.update_execution(
            execution,
            current_step=execution.current_step + 1,
            tool_call_count=execution.tool_call_count + 1,
        )
        return step

    async def complete_step(
        self, step: AgentExecutionStep, result_summary: str, latency_ms: int
    ) -> AgentExecutionStep:
        return await self.repository.update_step(
            step, status="COMPLETED", result_summary=result_summary, latency_ms=latency_ms
        )

    async def fail_step(
        self, step: AgentExecutionStep, error: str, latency_ms: int
    ) -> AgentExecutionStep:
        return await self.repository.update_step(
            step, status="FAILED", error=error, latency_ms=latency_ms
        )
