"""Agent orchestrator for managing tool-calling AI workflows.

This differs from the Sprint 2 AIOrchestrator by supporting
multi-step reasoning, native tool calling, and permission checks.
"""

import logging
import uuid
import json
from typing import Optional, Any

from app.agent.permissions import ToolPermissionService
from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools.base import ToolContext
from app.agent.tools.registry import ToolRegistry
from app.ai.context.builder import ContextBuilder
from app.ai.providers.base import AIProvider, AIMessage, MessageRole
from app.core.config import Settings
from app.models.conversation import Conversation
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
        conversation_id: Optional[uuid.UUID] = None,
    ) -> dict[str, Any]:
        """Execute the agent workflow for a user request."""
        # 1. Setup conversation and execution
        if conversation_id:
            conversation = await self.conversation_service.get_conversation(conversation_id, user.id)
            if not conversation:
                conversation = await self.conversation_service.create_conversation(user.id, prompt[:50])
        else:
            conversation = await self.conversation_service.create_conversation(user.id, prompt[:50])

        await self.conversation_service.add_message(
            conversation.id, role="user", content=prompt
        )

        execution = await self.execution_service.create_execution(
            user=user,
            conversation_id=conversation.id,
            objective=prompt,
            model=self.ai_provider.get_model_info().model,
        )
        execution = await self.execution_service.start_execution(execution)

        # 2. Build context
        workspace_context = await self.context_builder.build_context(user)
        system_content = f"{AGENT_SYSTEM_PROMPT}\n\nWorkspace Context:\n{workspace_context.formatted_text}"

        messages = [
            AIMessage(role=MessageRole.SYSTEM, content=system_content)
        ]

        # Load recent conversation history
        # (For simplicity in this implementation, we just use the current prompt, but in reality 
        # you'd load the last N messages from DB and convert them to AIMessage)
        messages.append(AIMessage(role=MessageRole.USER, content=prompt))

        # 3. Main Agent Loop
        steps_taken = 0
        final_content = ""
        tools = self.tool_registry.get_tool_definitions()

        try:
            while steps_taken < self.settings.AGENT_MAX_STEPS:
                steps_taken += 1
                
                # Call AI
                response = await self.ai_provider.generate(
                    messages=messages,
                    tools=tools,
                )

                # Add assistant message to history
                messages.append(AIMessage(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                ))

                if not response.tool_calls:
                    # AI is done, returned text
                    final_content = response.content
                    break

                # Process Tool Calls
                for tc in response.tool_calls:
                    tool_name = tc.name
                    tool_input = tc.arguments

                    # Record step
                    step = await self.execution_service.record_step(
                        execution=execution,
                        tool_name=tool_name,
                        tool_input=tool_input,
                    )

                    # Check permission
                    perm_result = await self.permission_service.check_tool_permission(
                        user, tool_name, tool_input
                    )

                    if not perm_result.allowed:
                        error_msg = f"Permission denied: {perm_result.reason}"
                        await self.execution_service.fail_step(step, error_msg, latency_ms=0)
                        messages.append(AIMessage(
                            role=MessageRole.TOOL,
                            content=json.dumps({"error": error_msg}),
                            tool_call_id=tc.id,
                            name=tool_name,
                        ))
                        continue

                    if perm_result.requires_approval:
                        await self.execution_service.update_execution(
                            execution, status="WAITING_FOR_APPROVAL"
                        )
                        msg = "This action requires your approval to proceed."
                        messages.append(AIMessage(
                            role=MessageRole.TOOL,
                            content=json.dumps({"status": "WAITING_FOR_APPROVAL", "message": msg}),
                            tool_call_id=tc.id,
                            name=tool_name,
                        ))
                        final_content = f"I need your approval to run `{tool_name}`."
                        break

                    # Execute Tool
                    tool = self.tool_registry.get(tool_name)
                    if not tool:
                        error_msg = f"Tool '{tool_name}' not found."
                        await self.execution_service.fail_step(step, error_msg, latency_ms=0)
                        messages.append(AIMessage(
                            role=MessageRole.TOOL,
                            content=json.dumps({"error": error_msg}),
                            tool_call_id=tc.id,
                            name=tool_name,
                        ))
                        continue

                    context = ToolContext(
                        user=user,
                        execution_id=execution.id,
                        conversation_id=conversation.id,
                        extra=self.extra_services,
                    )

                    # For actual execution, track latency (mocked here as 0)
                    result = await tool.execute(tool_input, context)

                    if result.success:
                        summary = f"Success"
                        await self.execution_service.complete_step(step, summary, latency_ms=100)
                        messages.append(AIMessage(
                            role=MessageRole.TOOL,
                            content=json.dumps(result.data or {"status": "success"}),
                            tool_call_id=tc.id,
                            name=tool_name,
                        ))
                    else:
                        summary = f"Failed: {result.error.get('message') if result.error else 'Unknown error'}"
                        await self.execution_service.fail_step(step, summary, latency_ms=100)
                        messages.append(AIMessage(
                            role=MessageRole.TOOL,
                            content=json.dumps({"error": result.error}),
                            tool_call_id=tc.id,
                            name=tool_name,
                        ))

                if execution.status == "WAITING_FOR_APPROVAL":
                    break

            if steps_taken >= self.settings.AGENT_MAX_STEPS:
                await self.execution_service.timeout_execution(execution)
                final_content = "I reached my maximum step limit before completing the task."

            if execution.status not in ("WAITING_FOR_APPROVAL", "TIMEOUT", "FAILED"):
                await self.execution_service.complete_execution(
                    execution,
                    input_tokens=0, # Need actual usage tracking
                    output_tokens=0,
                    total_tokens=0,
                )

            await self.conversation_service.add_message(
                conversation.id, role="assistant", content=final_content
            )

            return {
                "conversation_id": str(conversation.id),
                "execution_id": str(execution.id),
                "status": execution.status,
                "message": final_content,
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

