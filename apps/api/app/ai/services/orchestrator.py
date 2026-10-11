"""AI Orchestrator.

Orchestrates the complete AI pipeline:
Context Retrieval -> Prompt Assembly -> LLM Provider -> JSON Validation ->
Entity Resolution -> Domain Service Execution -> Response Synthesis & Logging.

CRITICAL: The LLM NEVER directly accesses the database.
All mutations and queries strictly go through existing domain services.
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.builder import AIContextBuilder
from app.ai.context.resolver import EntityResolver
from app.ai.errors import AIError, AIResponseError
from app.ai.prompts.system_prompt import build_system_prompt
from app.ai.providers import get_ai_provider
from app.ai.providers.base import AIMessage, BaseAIProvider
from app.ai.schemas.actions import ActionType
from app.ai.schemas.intent import ExtractedEntities, IntentType, ParsedIntent
from app.ai.schemas.responses import AIChatResponse, AIActionResult
from app.models.ai import AIRequestLog, Conversation, ConversationMessage
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskPriorityUpdate, TaskStatusUpdate
from app.services.client import ClientService
from app.services.dashboard import DashboardService
from app.services.project import ProjectService
from app.services.task import TaskService

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self, db: AsyncSession, provider: BaseAIProvider | None = None):
        self.db = db
        self.provider = provider or get_ai_provider()
        self.context_builder = AIContextBuilder(db)
        self.task_service = TaskService(db)
        self.project_service = ProjectService(db)
        self.client_service = ClientService(db)
        self.dashboard_service = DashboardService(db)

    async def _get_or_create_conversation(
        self, user_id: str, conversation_id: str | None, first_message: str
    ) -> Conversation:
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()
            if conv:
                return conv

        # Create new conversation
        short_title = (
            first_message[:40] + "..." if len(first_message) > 40 else first_message
        )
        new_conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=short_title or "New Conversation",
        )
        self.db.add(new_conv)
        await self.db.flush()
        return new_conv

    async def _get_recent_messages(
        self, conversation_id: str, limit: int = 10
    ) -> list[ConversationMessage]:
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    @staticmethod
    def _parse_llm_json(raw_text: str) -> dict[str, Any]:
        """Strip markdown ticks if present and parse JSON."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

        # Find first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIResponseError(f"Failed to parse LLM JSON response: {str(e)}") from e

    async def chat(
        self, user_id: str, message: str, conversation_id: str | None = None
    ) -> AIChatResponse:
        """Process a user message through the complete AI pipeline."""
        start_time = time.time()

        # 1. Manage Conversation & Save User Message
        conv = await self._get_or_create_conversation(user_id, conversation_id, message)

        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # 2. Build User-Scoped Context
        context = await self.context_builder.build(user_id=user_id)
        prompt_context_text = context.to_prompt_text()
        system_prompt = build_system_prompt(prompt_context_text)

        # 3. Assemble Messages for AI Provider
        recent_history = await self._get_recent_messages(conv.id, limit=6)
        ai_messages: list[AIMessage] = [AIMessage(role="system", content=system_prompt)]

        for h in recent_history:
            if h.id != user_msg.id:
                ai_messages.append(AIMessage(role=h.role, content=h.content))
        ai_messages.append(AIMessage(role="user", content=message))

        # 4. Generate Completion via AI Provider
        log_status = "SUCCESS"
        error_msg = None
        provider_name = getattr(self.provider, "_default_model", "ai-provider")

        try:
            ai_resp = await self.provider.generate(ai_messages, response_format={"type": "json_object"})
        except Exception as e:
            log_status = "ERROR"
            error_msg = str(e)
            logger.error("AI Provider generation failed: %s", e)
            # Log failure
            req_log = AIRequestLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                conversation_id=conv.id,
                provider=type(self.provider).__name__,
                model=provider_name,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=int((time.time() - start_time) * 1000),
                status=log_status,
                error_message=error_msg,
            )
            self.db.add(req_log)
            await self.db.commit()

            # Return fallback message
            fallback_text = "I'm having trouble connecting to the AI provider right now. Your workspace and tasks are safe and accessible directly via the dashboard."
            return AIChatResponse(
                message=fallback_text,
                conversation_id=conv.id,
                intent="ERROR",
                confidence=0.0,
                actions=[],
            )

        # 5. Record AI Request Log
        req_log = AIRequestLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conv.id,
            provider=type(self.provider).__name__,
            model=ai_resp.model or provider_name,
            prompt_tokens=ai_resp.input_tokens,
            completion_tokens=ai_resp.output_tokens,
            total_tokens=ai_resp.total_tokens,
            latency_ms=ai_resp.latency_ms,
            status=log_status,
        )
        self.db.add(req_log)

        # 6. Parse and Validate Structured Output
        try:
            parsed_dict = self._parse_llm_json(ai_resp.content)
            intent_val = parsed_dict.get("intent", "GENERAL_QUESTION")
            confidence = float(parsed_dict.get("confidence", 0.8))
            entities_raw = parsed_dict.get("entities", {}) or {}
            entities = ExtractedEntities(**entities_raw)
            reply = parsed_dict.get("reply", "")
            reasoning = parsed_dict.get("reasoning", "")
        except Exception as e:
            logger.warning("Failed to parse intent JSON, falling back to general question: %s", e)
            intent_val = "GENERAL_QUESTION"
            confidence = 0.5
            entities = ExtractedEntities()
            reply = ai_resp.content or "I couldn't clearly parse that request. Could you rephrase it?"
            reasoning = "Parsing fallback"

        # 7. Entity Resolution
        resolved = EntityResolver.resolve(
            context=context,
            project_ref=entities.project_name,
            client_ref=entities.client_name,
            task_ref=entities.task_reference or entities.task_title,
            raw_date=entities.due_date,
            raw_priority=entities.priority,
            raw_status=entities.status,
        )

        # 8. Check for Ambiguity
        if resolved.ambiguous_matches:
            ambig_str = ", ".join(resolved.ambiguous_matches)
            clarify_text = f"I found multiple matches ({ambig_str}). Which one did you mean?"
            bot_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id=conv.id,
                role="assistant",
                content=clarify_text,
                intent="CLARIFY",
                confidence=confidence,
                tokens_used=ai_resp.total_tokens,
            )
            self.db.add(bot_msg)
            await self.db.commit()
            return AIChatResponse(
                message=clarify_text,
                conversation_id=conv.id,
                intent="CLARIFY",
                confidence=confidence,
                actions=[],
            )

        # 9. Execute Actions via Domain Services
        actions: list[AIActionResult] = []
        final_message = reply

        try:
            if intent_val == IntentType.CREATE_TASK.value or intent_val == "CREATE_TASK":
                title = entities.task_title or message
                # Priority
                priority = resolved.priority or TaskPriority.MEDIUM
                # Status
                status = resolved.status or TaskStatus.TODO

                create_payload = TaskCreate(
                    title=title,
                    description=entities.task_description,
                    project_id=resolved.project_id,
                    client_id=resolved.client_id,
                    priority=priority,
                    status=status,
                    due_date=resolved.due_date,
                    estimated_minutes=entities.estimated_minutes,
                    labels=entities.labels if entities.labels else None,
                )

                created_task = await self.task_service.create(user_id=user_id, data=create_payload)

                proj_msg = f" for project '{resolved.project_name}'" if resolved.project_name else ""
                due_msg = f", due {resolved.due_date.isoformat()}" if resolved.due_date else ""
                final_message = (
                    f"Created task '{created_task.title}' ({priority.value} priority{due_msg}){proj_msg}."
                )
                actions.append(
                    AIActionResult(
                        type="TASK_CREATED",
                        success=True,
                        message=f"Created task: {created_task.title}",
                        data={"task_id": created_task.id, "title": created_task.title},
                    )
                )

            elif intent_val == IntentType.COMPLETE_TASK.value or intent_val == "COMPLETE_TASK":
                target_task_id = resolved.task_id
                if not target_task_id and context.recent_tasks:
                    # If user just said "mark task as completed", check single task or title match
                    ref = entities.task_reference or entities.task_title or ""
                    for t in context.recent_tasks:
                        if ref.lower() in t["title"].lower():
                            target_task_id = t["id"]
                            resolved.task_title = t["title"]
                            break

                if target_task_id:
                    updated = await self.task_service.change_status(
                        user_id=user_id,
                        task_id=target_task_id,
                        data=TaskStatusUpdate(status=TaskStatus.COMPLETED),
                    )
                    final_message = f"Marked task '{updated.title}' as COMPLETED."
                    actions.append(
                        AIActionResult(
                            type="TASK_COMPLETED",
                            success=True,
                            message=f"Completed task: {updated.title}",
                            data={"task_id": updated.id, "status": "COMPLETED"},
                        )
                    )
                else:
                    final_message = "I couldn't locate the task you want to mark as completed. Could you specify the exact task title?"

            elif intent_val == IntentType.CHANGE_TASK_STATUS.value or intent_val == "CHANGE_TASK_STATUS":
                target_task_id = resolved.task_id
                target_status = resolved.status or TaskStatus.IN_PROGRESS

                if not target_task_id and context.recent_tasks:
                    ref = entities.task_reference or entities.task_title or ""
                    for t in context.recent_tasks:
                        if ref and ref.lower() in t["title"].lower():
                            target_task_id = t["id"]
                            break

                if target_task_id:
                    updated = await self.task_service.change_status(
                        user_id=user_id,
                        task_id=target_task_id,
                        data=TaskStatusUpdate(status=target_status),
                    )
                    final_message = f"Moved task '{updated.title}' to status {target_status.value}."
                    actions.append(
                        AIActionResult(
                            type="STATUS_CHANGED",
                            success=True,
                            message=f"Changed status to {target_status.value}",
                            data={"task_id": updated.id, "status": target_status.value},
                        )
                    )
                else:
                    final_message = f"I couldn't find the task to change status to {target_status.value}."

            elif intent_val == IntentType.CHANGE_TASK_PRIORITY.value or intent_val == "CHANGE_TASK_PRIORITY":
                target_task_id = resolved.task_id
                target_prio = resolved.priority or TaskPriority.HIGH

                if not target_task_id and context.recent_tasks:
                    ref = entities.task_reference or entities.task_title or ""
                    for t in context.recent_tasks:
                        if ref and ref.lower() in t["title"].lower():
                            target_task_id = t["id"]
                            break

                if target_task_id:
                    updated = await self.task_service.change_priority(
                        user_id=user_id,
                        task_id=target_task_id,
                        data=TaskPriorityUpdate(priority=target_prio),
                    )
                    final_message = f"Set priority of '{updated.title}' to {target_prio.value}."
                    actions.append(
                        AIActionResult(
                            type="PRIORITY_CHANGED",
                            success=True,
                            message=f"Changed priority to {target_prio.value}",
                            data={"task_id": updated.id, "priority": target_prio.value},
                        )
                    )
                else:
                    final_message = f"I couldn't find the task to set priority to {target_prio.value}."

            elif intent_val == IntentType.GET_TODAY_TASKS.value or intent_val == "GET_TODAY_TASKS":
                dashboard = await self.dashboard_service.get_today_dashboard(user_id=user_id)
                due_count = len(dashboard.due_today)
                overdue_count = len(dashboard.overdue)

                lines = [f"Here is your workload for today ({dashboard.date.isoformat()}):"]
                if due_count > 0:
                    lines.append(f"\nTasks Due Today ({due_count}):")
                    for t in dashboard.due_today:
                        lines.append(f"- [{t.priority.value}] {t.title} ({t.status.value})")
                else:
                    lines.append("\nNo tasks due today.")

                if overdue_count > 0:
                    lines.append(f"\nOverdue Tasks ({overdue_count}):")
                    for t in dashboard.overdue:
                        lines.append(f"- [OVERDUE] {t.title} ({t.priority.value})")

                final_message = "\n".join(lines)
                actions.append(
                    AIActionResult(
                        type="GET_TODAY_DASHBOARD",
                        success=True,
                        message=f"{due_count} tasks due today, {overdue_count} overdue",
                        data={"due_today": due_count, "overdue": overdue_count},
                    )
                )

            elif intent_val == IntentType.GET_OVERDUE_TASKS.value or intent_val == "GET_OVERDUE_TASKS":
                dashboard = await self.dashboard_service.get_today_dashboard(user_id=user_id)
                overdue_count = len(dashboard.overdue)
                if overdue_count == 0:
                    final_message = "Great news! You have no overdue tasks."
                else:
                    lines = [f"You have {overdue_count} overdue task(s):"]
                    for t in dashboard.overdue:
                        lines.append(f"- {t.title} (Priority: {t.priority.value}, Due: {t.due_date})")
                    final_message = "\n".join(lines)

                actions.append(
                    AIActionResult(
                        type="GET_OVERDUE_TASKS",
                        success=True,
                        message=f"{overdue_count} overdue tasks",
                        data={"count": overdue_count},
                    )
                )

            elif intent_val == IntentType.SEARCH_TASKS.value or intent_val == "SEARCH_TASKS":
                query = entities.search_query or ""
                search_results = await self.task_service.search(user_id=user_id, query=query)
                if not search_results:
                    final_message = f"No tasks found matching '{query}'."
                else:
                    lines = [f"Found {len(search_results)} matching task(s) for '{query}':"]
                    for t in search_results[:10]:
                        lines.append(f"- [{t.status.value}] {t.title} ({t.priority.value} priority)")
                    final_message = "\n".join(lines)

                actions.append(
                    AIActionResult(
                        type="SEARCH_TASKS",
                        success=True,
                        message=f"Found {len(search_results)} tasks",
                        data={"count": len(search_results)},
                    )
                )

            elif intent_val == IntentType.GET_PROJECT_INFO.value or intent_val == "GET_PROJECT_INFO":
                if resolved.project_id:
                    proj = await self.project_service.get(user_id=user_id, project_id=resolved.project_id)
                    final_message = (
                        f"Project: {proj.name}\n"
                        f"Status: {proj.status.value}\n"
                        f"Description: {proj.description or 'None'}\n"
                        f"Summary: {proj.task_summary}"
                    )
                    actions.append(
                        AIActionResult(
                            type="GET_PROJECT_INFO",
                            success=True,
                            message=f"Project info for {proj.name}",
                            data={"project_id": proj.id, "name": proj.name},
                        )
                    )
                else:
                    final_message = (
                        f"I couldn't find a project matching '{entities.project_name}'. "
                        f"Your active projects are: {', '.join([p['name'] for p in context.projects]) or 'None'}."
                    )

            elif intent_val == IntentType.GET_CLIENT_INFO.value or intent_val == "GET_CLIENT_INFO":
                if resolved.client_id:
                    client = await self.client_service.get(user_id=user_id, client_id=resolved.client_id)
                    final_message = (
                        f"Client: {client.name}\n"
                        f"Company: {client.company_name or 'N/A'}\n"
                        f"Email: {client.email or 'N/A'}\n"
                        f"Status: {client.status.value}"
                    )
                    actions.append(
                        AIActionResult(
                            type="GET_CLIENT_INFO",
                            success=True,
                            message=f"Client info for {client.name}",
                            data={"client_id": client.id, "name": client.name},
                        )
                    )
                else:
                    final_message = (
                        f"I couldn't find a client matching '{entities.client_name}'. "
                        f"Your active clients are: {', '.join([c['name'] for c in context.clients]) or 'None'}."
                    )

            else:
                # GENERAL_QUESTION
                if not final_message:
                    final_message = "I am TaskMate AI, your workspace assistant. How can I assist you with your tasks or projects?"

        except Exception as e:
            logger.error("Error executing domain action for intent %s: %s", intent_val, e)
            final_message = f"I understood your request ({intent_val}), but encountered an error: {str(e)}"
            actions.append(
                AIActionResult(
                    type="ERROR",
                    success=False,
                    message=str(e),
                )
            )

        # 10. Persist Assistant Response in Conversation
        bot_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="assistant",
            content=final_message,
            intent=intent_val,
            confidence=confidence,
            raw_entities=json.dumps(entities.model_dump()),
            tokens_used=ai_resp.total_tokens,
        )
        self.db.add(bot_msg)
        await self.db.commit()

        # 11. Return Response
        return AIChatResponse(
            message=final_message,
            conversation_id=conv.id,
            intent=intent_val,
            confidence=confidence,
            actions=actions,
            context_summary={
                "projects_count": len(context.projects),
                "tasks_count": len(context.recent_tasks),
            },
        )

