"""Repository for agent execution persistence."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_execution import AgentExecution, AgentExecutionStep


class AgentExecutionRepository:
    """Data access for agent executions and steps."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_execution(
        self, user_id: uuid.UUID, conversation_id: Optional[uuid.UUID] = None,
        objective: Optional[str] = None, model: Optional[str] = None,
    ) -> AgentExecution:
        execution = AgentExecution(
            user_id=user_id,
            conversation_id=conversation_id,
            objective=objective,
            model=model,
            status="PENDING",
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def get_execution(
        self, execution_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[AgentExecution]:
        stmt = (
            select(AgentExecution)
            .options(selectinload(AgentExecution.steps))
            .where(
                AgentExecution.id == execution_id,
                AgentExecution.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_execution(
        self, execution: AgentExecution, **kwargs: Any
    ) -> AgentExecution:
        for key, value in kwargs.items():
            setattr(execution, key, value)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def add_step(
        self, execution_id: uuid.UUID, step_number: int,
        tool_name: str, tool_input: Optional[dict] = None,
    ) -> AgentExecutionStep:
        step = AgentExecutionStep(
            execution_id=execution_id,
            step_number=step_number,
            tool_name=tool_name,
            tool_input=tool_input,
            status="PENDING",
        )
        self.session.add(step)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def update_step(
        self, step: AgentExecutionStep, **kwargs: Any
    ) -> AgentExecutionStep:
        for key, value in kwargs.items():
            setattr(step, key, value)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def cancel_execution(
        self, execution_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[AgentExecution]:
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
