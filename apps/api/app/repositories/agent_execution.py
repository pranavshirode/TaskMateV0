"""Repository for agent execution persistence."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_execution import AgentExecution, AgentExecutionStep


class AgentExecutionRepository:
    """Data access for agent executions and steps."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_execution(
        self,
        user_id: str | uuid.UUID,
        conversation_id: str | uuid.UUID | None = None,
        objective: str | None = None,
        model: str | None = None,
    ) -> AgentExecution:
        execution = AgentExecution(
            user_id=str(user_id),
            conversation_id=str(conversation_id) if conversation_id else None,
            objective=objective,
            model=model,
            status="PENDING",
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def get_execution(self, execution_id: str | uuid.UUID, user_id: str | uuid.UUID) -> AgentExecution | None:
        stmt = (
            select(AgentExecution)
            .options(selectinload(AgentExecution.steps))
            .where(
                AgentExecution.id == str(execution_id),
                AgentExecution.user_id == str(user_id),
            )
            # Always reflect the database: status may have been changed by transition_status().
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_execution(self, execution: AgentExecution, **kwargs: Any) -> AgentExecution:
        for key, value in kwargs.items():
            setattr(execution, key, value)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def add_step(
        self,
        execution_id: uuid.UUID,
        step_number: int,
        tool_name: str,
        tool_input: dict | None = None,
        status: str = "PENDING",
        result_summary: str | None = None,
        latency_ms: int = 0,
        error: str | None = None,
    ) -> AgentExecutionStep:
        step = AgentExecutionStep(
            execution_id=execution_id,
            step_number=step_number,
            tool_name=tool_name,
            tool_input=tool_input,
            status=status,
            result_summary=result_summary,
            latency_ms=latency_ms,
            error=error,
        )
        self.session.add(step)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def update_step(self, step: AgentExecutionStep, **kwargs: Any) -> AgentExecutionStep:
        for key, value in kwargs.items():
            setattr(step, key, value)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def transition_status(self, execution_id: str, user_id: str, from_status: str, to_status: str) -> bool:
        """Atomically move an execution between states; False if it was not in `from_status`.

        Used so an approval can only be acted on once, even with concurrent or repeated requests.
        """
        result = await self.session.execute(
            update(AgentExecution)
            .where(
                AgentExecution.id == str(execution_id),
                AgentExecution.user_id == str(user_id),
                AgentExecution.status == from_status,
            )
            .values(status=to_status)
        )
        await self.session.commit()
        return result.rowcount == 1  # type: ignore[attr-defined]  # CursorResult for UPDATE statements

    async def cancel_execution(self, execution_id: uuid.UUID, user_id: uuid.UUID) -> AgentExecution | None:
        execution = await self.get_execution(execution_id, user_id)
        if not execution:
            return None
        if execution.status in ("COMPLETED", "FAILED", "CANCELLED"):
            return execution  # Already terminal
        execution.status = "CANCELLED"
        execution.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution
