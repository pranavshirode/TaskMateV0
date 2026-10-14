"""Agent orchestrator for managing tool-calling AI workflows.

This differs from the Sprint 2 AIOrchestrator by supporting
multi-step reasoning, native tool calling, and permission checks.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.agent.permissions import ToolPermissionService
from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools.base import ToolContext, ToolResult
from app.agent.tools.registry import ToolRegistry
from app.ai.context.builder import ContextBuilder
from app.ai.providers.base import AIMessage, AIProvider, MessageRole
from app.core.config import Settings
from app.core.errors import ConflictError, NotFoundError
from app.models.user import User
from app.services.agent_execution import AgentExecutionService
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Manages multi-step agent execution with tool calling."""

    def __init__(
        self,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        permission_service: ToolPermissionService,
        context_builder: ContextBuilder,
        execution_service: AgentExecutionService,
        conversation_service: ConversationService,
        settings: Settings,
        **extra_services: Any,
    ):
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry
        self.permission_service = permission_service
        self.context_builder = context_builder
        self.execution_service = execution_service
        self.conversation_service = conversation_service
        self.settings = settings
        self.extra_services = extra_services

    async def run_agent(
        self,
        user: User,
        prompt: str,
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Execute the agent workflow for a user request."""
        # 1. Setup conversation and execution
        # Falls back to a new conversation if the id is unknown or belongs to another user.
        conversation = await self.conversation_service.get_or_create_conversation(user, conversation_id)
        if not conversation.title:
            await self.conversation_service.update_title(conversation, prompt[:50])

        await self.conversation_service.add_user_message(conversation.id, prompt)

        execution = await self.execution_service.create_execution(
            user=user,
            conversation_id=conversation.id,
            objective=prompt,
            model=self.ai_provider.get_model_info().model,
        )
        execution = await self.execution_service.start_execution(execution)

        # 2. Build context
        workspace_context = await self.context_builder.build(str(user.id))
        system_content = f"{AGENT_SYSTEM_PROMPT}\n\nWorkspace Context:\n{workspace_context.to_prompt_text()}"

        messages = [AIMessage(role=MessageRole.SYSTEM, content=system_content)]

        # Load recent conversation history
        # (For simplicity in this implementation, we just use the current prompt, but in reality
        # you'd load the last N messages from DB and convert them to AIMessage)
        messages.append(AIMessage(role=MessageRole.USER, content=prompt))

        # 3. Main Agent Loop
        tools = self.tool_registry.get_tool_definitions()
        final_content = ""
        tool_calls_made = 0
        input_tokens = output_tokens = 0
        started = time.monotonic()
        # Set when the loop stops early; None means the model produced a final answer.
        stop_reason: str | None = None
        pending_action: dict[str, Any] | None = None

        def tool_message(tc: Any, payload: dict[str, Any]) -> AIMessage:
            return AIMessage(role=MessageRole.TOOL, content=json.dumps(payload), tool_call_id=tc.id, name=tc.name)

        try:
            for _ in range(self.settings.AGENT_MAX_STEPS):
                if time.monotonic() - started > self.settings.AGENT_MAX_EXECUTION_TIME:
                    stop_reason = "time"
                    break

                response = await self.ai_provider.generate(messages=messages, tools=tools)
                input_tokens += response.input_tokens
                output_tokens += response.output_tokens

                messages.append(
                    AIMessage(role=MessageRole.ASSISTANT, content=response.content, tool_calls=response.tool_calls)
                )

                if not response.tool_calls:
                    final_content = response.content
                    break

                for tc in response.tool_calls:
                    if tool_calls_made >= self.settings.AGENT_MAX_TOOL_CALLS:
                        stop_reason = "tool_calls"
                        break
                    tool_calls_made += 1

                    step = await self.execution_service.record_step(
                        execution=execution,
                        step_number=tool_calls_made,
                        tool_name=tc.name,
                        tool_input=tc.arguments,
                    )

                    perm_result = await self.permission_service.check_tool_permission(user, tc.name, tc.arguments)
                    if not perm_result.allowed:
                        error_msg = f"Permission denied: {perm_result.reason}"
                        await self.execution_service.fail_step(step, error_msg)
                        messages.append(tool_message(tc, {"error": error_msg}))
                        continue

                    if perm_result.requires_approval:
                        # The step keeps the exact tool input; POST /agent/executions/{id}/approve runs it.
                        await self.execution_service.update_execution(execution, status="WAITING_FOR_APPROVAL")
                        await self.execution_service.update_step(step, status="PENDING")
                        stop_reason = "approval"
                        pending_action = {
                            "step_id": str(step.id),
                            "tool_name": tc.name,
                            "arguments": tc.arguments,
                            "summary": describe_action(tc.name, tc.arguments),
                        }
                        final_content = f"I need your approval to {pending_action['summary'][0].lower()}{pending_action['summary'][1:]}."
                        break

                    tool = self.tool_registry.get(tc.name)
                    if not tool:
                        error_msg = f"Tool '{tc.name}' not found."
                        await self.execution_service.fail_step(step, error_msg)
                        messages.append(tool_message(tc, {"error": error_msg}))
                        continue

                    context = ToolContext(
                        user=user,
                        execution_id=execution.id,
                        conversation_id=conversation.id,
                        extra=self.extra_services,
                    )
                    tool_started = time.monotonic()
                    try:
                        result = await tool.execute(tc.arguments, context)
                    except Exception as exc:  # A failing tool fails its step, not the whole run.
                        logger.exception("Tool %s raised", tc.name)
                        latency = int((time.monotonic() - tool_started) * 1000)
                        await self.execution_service.fail_step(step, f"Tool error: {exc}", latency_ms=latency)
                        messages.append(tool_message(tc, {"error": "The tool failed unexpectedly."}))
                        continue
                    latency = int((time.monotonic() - tool_started) * 1000)

                    if result.success:
                        await self.execution_service.complete_step(step, "Success", latency_ms=latency)
                        messages.append(tool_message(tc, result.data or {"status": "success"}))
                    else:
                        message = result.error.get("message") if result.error else "Unknown error"
                        await self.execution_service.fail_step(step, f"Failed: {message}", latency_ms=latency)
                        messages.append(tool_message(tc, {"error": result.error}))

                if stop_reason:
                    break
            else:
                # The step budget ran out while the model was still calling tools.
                stop_reason = "steps"

            token_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
            if stop_reason in ("steps", "tool_calls", "time"):
                limit = {"steps": "step", "tool_calls": "tool-call", "time": "time"}[stop_reason]
                await self.execution_service.update_execution(
                    execution,
                    status="TIMEOUT",
                    error=f"Agent {limit} limit reached",
                    completed_at=datetime.now(timezone.utc),
                    **token_usage,
                )
                final_content = f"I reached my {limit} limit before completing the task."
            elif stop_reason == "approval":
                await self.execution_service.update_execution(execution, **token_usage)
            else:
                await self.execution_service.complete_execution(execution, **token_usage)

            await self.conversation_service.add_assistant_message(conversation.id, final_content)

            return {
                "conversation_id": str(conversation.id),
                "execution_id": str(execution.id),
                "status": execution.status,
                "message": final_content,
                "pending_action": pending_action,
            }

        except Exception as e:
            logger.exception("Agent execution failed")
            await self.execution_service.fail_execution(execution, str(e))
            return {
                "conversation_id": str(conversation.id),
                "execution_id": str(execution.id),
                "status": "FAILED",
                "message": "An internal error occurred during agent execution.",
            }

    async def resolve_pending(self, user: User, execution_id: str, approve: bool) -> dict[str, Any]:
        """Approve (run) or reject the single action an execution is waiting on.

        The status change is atomic, so an action can never run twice (double click, retries, replays).
        """
        target = "RUNNING" if approve else "CANCELLED"
        if not await self.execution_service.transition_status(execution_id, user, "WAITING_FOR_APPROVAL", target):
            if await self.execution_service.get_execution(execution_id, user) is None:
                raise NotFoundError("Agent execution not found")
            raise ConflictError("This action has already been approved, rejected or expired.", code="NOT_PENDING")

        execution = await self.execution_service.get_execution(execution_id, user)
        assert execution is not None
        step = next((s for s in reversed(execution.steps) if s.status == "PENDING"), None)
        if step is None:  # Should not happen; fail closed rather than guess what to run.
            await self.execution_service.fail_execution(execution, "No pending step found")
            raise ConflictError("There is no pending action on this execution.", code="NOT_PENDING")

        summary = describe_action(step.tool_name, step.tool_input or {})
        result_data: dict[str, Any] | None = None

        if not approve:
            await self.execution_service.update_step(step, status="SKIPPED", result_summary="Rejected by user")
            await self.execution_service.update_execution(execution, completed_at=datetime.now(timezone.utc))
            message = f"Okay, I did not {summary[0].lower()}{summary[1:]}."
        else:
            # Re-check authorisation at execution time; approval never bypasses access rules.
            perm = await self.permission_service.check_tool_permission(user, step.tool_name, step.tool_input or {})
            tool = self.tool_registry.get(step.tool_name)
            if not perm.allowed or tool is None:
                reason = perm.reason if not perm.allowed else "tool is no longer available"
                await self.execution_service.fail_step(step, f"Permission denied: {reason}")
                await self.execution_service.fail_execution(execution, f"Permission denied: {reason}")
                message = f"I couldn't {summary[0].lower()}{summary[1:]}: {reason}."
            else:
                context = ToolContext(
                    user=user,
                    execution_id=execution.id,
                    conversation_id=execution.conversation_id,
                    extra=self.extra_services,
                )
                started = time.monotonic()
                try:
                    result = await tool.execute(step.tool_input or {}, context)
                except Exception as exc:
                    logger.exception("Approved tool %s raised", step.tool_name)
                    result = ToolResult.fail("INTERNAL_ERROR", str(exc))
                latency = int((time.monotonic() - started) * 1000)
                if result.success:
                    result_data = result.data
                    await self.execution_service.complete_step(step, "Success", latency_ms=latency)
                    await self.execution_service.complete_execution(execution)
                    message = f"Done: {summary[0].lower()}{summary[1:]}."
                else:
                    error = result.error.get("message") if result.error else "Unknown error"
                    await self.execution_service.fail_step(step, f"Failed: {error}", latency_ms=latency)
                    await self.execution_service.fail_execution(execution, error)
                    message = f"I tried to {summary[0].lower()}{summary[1:]}, but it failed: {error}"

        if execution.conversation_id:
            await self.conversation_service.add_assistant_message(execution.conversation_id, message)

        return {
            "conversation_id": execution.conversation_id,
            "execution_id": str(execution.id),
            "status": execution.status,
            "message": message,
            "result": result_data,
        }


TOOL_ACTIONS = {
    "task.create": "Create task",
    "task.update": "Update task",
    "task.change_status": "Change task status",
    "task.change_priority": "Change task priority",
}


def describe_action(tool_name: str, arguments: dict[str, Any]) -> str:
    """Short human-readable description of a tool call, shown on the approval card."""
    label = TOOL_ACTIONS.get(tool_name, f"Run {tool_name}")
    details = []
    if arguments.get("title"):
        details.append(f'"{arguments["title"]}"')
    for key in ("status", "priority", "due_date"):
        if arguments.get(key):
            details.append(f"{key.replace('_', ' ')} {arguments[key]}")
    return f"{label} {' · '.join(details)}".strip()
