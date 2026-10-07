import json
import logging
import time
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from pydantic import ValidationError

from app.models.user import User
from app.ai.providers.base import AIProvider, AIMessage, MessageRole
from app.ai.schemas.intent import IntentType, IntentResult, ExtractedEntities
from app.ai.schemas.responses import AIChatResponse, AIActionResult, ContextSummary
from app.ai.context.builder import ContextBuilder, WorkspaceContext
from app.ai.context.resolver import EntityResolver, ResolutionStatus, ResolutionResult
from app.ai.prompts.system import SYSTEM_PROMPT
from app.ai.errors import AIError, AIResponseError
from app.services.task import TaskService
from app.services.project import ProjectService
from app.services.client import ClientService
from app.services.dashboard import DashboardService
from app.services.conversation import ConversationService
from app.schemas.task import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """AI Orchestrator that connects user messages to AI reasoning and backend actions."""

    def __init__(
        self,
        ai_provider: AIProvider,
        context_builder: ContextBuilder,
        entity_resolver: EntityResolver,
        conversation_service: ConversationService,
        task_service: TaskService,
        project_service: ProjectService,
        client_service: ClientService,
        dashboard_service: DashboardService,
    ):
        self.ai_provider = ai_provider
        self.context_builder = context_builder
        self.entity_resolver = entity_resolver
        self.conversation_service = conversation_service
        self.task_service = task_service
        self.project_service = project_service
        self.client_service = client_service
        self.dashboard_service = dashboard_service

    async def chat(
        self, user: User, message: str, conversation_id: Optional[UUID] = None
    ) -> AIChatResponse:
        """Handle a chat message from the user, determining intent and executing actions."""
        start_time = time.time()

        provider_model = "unknown"
        intent_type = None
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        error_type = None
        status = "success"

        try:
            # 1. Get or create conversation
            conversation = await self.conversation_service.get_or_create_conversation(
                user=user, conversation_id=conversation_id
            )
            conv_id = conversation.id

            # 2. Save user message
            await self.conversation_service.add_user_message(conv_id, message)

            # 3. Build workspace context
            context = await self.context_builder.build_context(user)

            # 4. Get conversation history
            recent_messages = await self.conversation_service.get_recent_messages(conv_id, limit=10)

            # 5. Construct messages for AI
            system_content = SYSTEM_PROMPT.template.format(
                current_date=datetime.now().strftime("%Y-%m-%d"),
                user_name=user.full_name or user.email,
                workspace_context=context.formatted_text
            )

            ai_messages = [AIMessage(role=MessageRole.SYSTEM, content=system_content)]

            # Add history, excluding the just added user message (we'll add it last)
            history_msgs = recent_messages[:-1] if recent_messages else []
            for msg in history_msgs:
                role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
                ai_messages.append(AIMessage(role=role, content=msg.content))

            ai_messages.append(AIMessage(role=MessageRole.USER, content=message))

            # 6. Call AI Provider
            ai_response = await self.ai_provider.generate(
                messages=ai_messages,
                response_format={"type": "json_object"}
            )

            provider_model = ai_response.model
            input_tokens = ai_response.usage.input_tokens
            output_tokens = ai_response.usage.output_tokens
            total_tokens = ai_response.usage.total_tokens

            # 7. Parse AI Response
            try:
                response_dict = json.loads(ai_response.content)
                # Normalize keys or handle raw JSON
                intent = response_dict.get("intent", IntentType.GENERAL_QUESTION)
                try:
                    intent_type = IntentType(intent)
                except ValueError:
                    intent_type = IntentType.GENERAL_QUESTION

                confidence = float(response_dict.get("confidence", 1.0))
                entities_dict = response_dict.get("entities", {})
                reasoning = response_dict.get("reasoning", "")
                ai_reply_message = response_dict.get("message", "I have processed your request.")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise AIResponseError("Failed to parse response from AI")

            # 8. Check confidence and process actions
            requires_clarification = False
            action_results = []
            suggestions = []
            final_message = ai_reply_message

            if confidence < 0.4:
                requires_clarification = True
                final_message = f"I'm not entirely sure what you mean. {ai_reply_message}"
            else:
                # 9. Execute based on intent
                if confidence < 0.7:
                    final_message = f"I think you want to {intent_type.value}, but I'm not entirely sure. " + final_message

                try:
                    entities = ExtractedEntities(**entities_dict)
                    action_result, action_clarify, action_msg = await self._execute_action(
                        intent_type, entities, user, context
                    )
                    if action_result:
                        action_results.append(action_result)

                    if action_clarify:
                        requires_clarification = True

                    if action_msg:
                        final_message = action_msg

                except ValidationError as e:
                    logger.error(f"Failed to validate entities: {e}")
                    raise AIResponseError("Failed to validate extracted entities")

            # 10. Update conversation title if first message
            if not conversation.title or conversation.title == "New Conversation":
                title_suggestion = message[:40] + "..." if len(message) > 40 else message
                await self.conversation_service.update_title(conversation, title_suggestion)

            # 11. Save assistant message
            await self.conversation_service.add_assistant_message(
                conversation_id=conv_id,
                content=final_message,
                intent=intent_type.value if intent_type else None
            )

            # 12. Return Response
            return AIChatResponse(
                message=final_message,
                intent=intent_type,
                confidence=confidence,
                actions=action_results,
                conversation_id=conv_id,
                context_summary=context.summary,
                requires_clarification=requires_clarification,
                suggestions=suggestions
            )

        except AIError as e:
            error_type = e.__class__.__name__
            status = "error"
            logger.error(f"AIError during chat: {e}")
            return self._build_error_response(conversation_id, str(e), error_type)
        except Exception as e:
            error_type = "InternalError"
            status = "error"
            logger.exception(f"Unexpected error during chat: {e}")
            return self._build_error_response(
                conversation_id,
                "An unexpected error occurred while processing your request.",
                error_type
            )
        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            await self.conversation_service.log_ai_request(
                user_id=user.id,
                provider=self.ai_provider.__class__.__name__,
                model=provider_model,
                intent=intent_type.value if intent_type else None,
                conversation_id=conversation_id,
                status=status,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                error_type=error_type
            )

    def _build_error_response(
        self, conversation_id: Optional[UUID], message: str, error_type: str
    ) -> AIChatResponse:
        return AIChatResponse(
            message=message,
            intent=None,
            confidence=0.0,
            actions=[
                AIActionResult(
                    action_type=IntentType.GENERAL_QUESTION,
                    success=False,
                    data=None,
                    error=error_type
                )
            ],
            conversation_id=conversation_id or UUID(int=0),
            context_summary=None,
            requires_clarification=True,
            suggestions=[]
        )

    async def _execute_action(
        self, intent: IntentType, entities: ExtractedEntities, user: User, context: WorkspaceContext
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        """Route to the correct handler based on intent."""
        try:
            if intent == IntentType.CREATE_TASK:
                return await self._handle_create_task(entities, user)
            elif intent == IntentType.UPDATE_TASK:
                return await self._handle_update_task(entities, user)
            elif intent == IntentType.COMPLETE_TASK:
                return await self._handle_complete_task(entities, user)
            elif intent == IntentType.CHANGE_TASK_STATUS:
                return await self._handle_change_status(entities, user)
            elif intent == IntentType.CHANGE_TASK_PRIORITY:
                return await self._handle_change_priority(entities, user)
            elif intent == IntentType.SEARCH_TASKS:
                return await self._handle_search_tasks(entities, user)
            elif intent == IntentType.GET_TODAY_TASKS:
                return await self._handle_get_today_tasks(user)
            elif intent == IntentType.GET_OVERDUE_TASKS:
                return await self._handle_get_overdue_tasks(user)
            elif intent == IntentType.GET_PROJECT_INFO:
                return await self._handle_get_project_info(entities, user)
            elif intent == IntentType.GET_CLIENT_INFO:
                return await self._handle_get_client_info(entities, user)
            elif intent == IntentType.GENERAL_QUESTION:
                return None, False, None
            else:
                return None, False, "I didn't understand that action."
        except Exception as e:
            logger.error(f"Error executing action {intent}: {e}")
            action_res = AIActionResult(
                action_type=intent, success=False, error="Failed to execute action."
            )
            return action_res, False, "I ran into an issue while trying to do that."

    async def _handle_create_task(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        if not entities.title:
            return None, True, "What should I set as the task title?"

        # Resolve Project
        project_id = None
        if entities.project_name:
            res = await self.entity_resolver.resolve_project(entities.project_name, user)
            if res.status == ResolutionStatus.AMBIGUOUS:
                cands = ", ".join([c["name"] for c in res.candidates])
                return None, True, f"Which project do you mean? Options: {cands}"
            elif res.status == ResolutionStatus.NOT_FOUND:
                return None, True, f"I couldn't find a project named '{entities.project_name}'."
            project_id = res.entity_id

        # Resolve Client
        client_id = None
        if entities.client_name:
            res = await self.entity_resolver.resolve_client(entities.client_name, user)
            if res.status == ResolutionStatus.AMBIGUOUS:
                cands = ", ".join([c["name"] for c in res.candidates])
                return None, True, f"Which client do you mean? Options: {cands}"
            elif res.status == ResolutionStatus.NOT_FOUND:
                return None, True, f"I couldn't find a client named '{entities.client_name}'."
            client_id = res.entity_id

        # Resolve Priority & Date
        priority = "MEDIUM"
        if entities.priority:
            priority = self.entity_resolver.resolve_priority(entities.priority) or "MEDIUM"

        due_date = None
        if entities.due_date:
            due_date = self.entity_resolver.resolve_date(entities.due_date)

        task_in = TaskCreate(
            title=entities.title,
            description=entities.description,
            project_id=project_id,
            client_id=client_id,
            priority=priority,
            due_date=due_date,
            source="ai_assistant"
        )

        task = await self.task_service.create_task(user, task_in)

        result = AIActionResult(
            action_type=IntentType.CREATE_TASK,
            success=True,
            data={"task_id": str(task.id), "title": task.title}
        )
        return result, False, f"Created task '{task.title}' successfully."

    async def _resolve_target_task(
        self, task_name: Optional[str], user: User
    ) -> Tuple[Optional[UUID], Optional[str], bool]:
        """Helper to resolve task. Returns (task_id, msg, requires_clarification)"""
        if not task_name:
            return None, "Which task do you mean?", True

        res = await self.entity_resolver.resolve_task(task_name, user)
        if res.status == ResolutionStatus.AMBIGUOUS:
            cands = ", ".join([c["title"] for c in res.candidates])
            return None, f"Which task do you mean? Found: {cands}", True
        elif res.status == ResolutionStatus.NOT_FOUND:
            return None, f"I couldn't find a task named '{task_name}'.", True

        return res.entity_id, None, False

    async def _handle_update_task(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        task_id, msg, clarify = await self._resolve_target_task(entities.task_name or entities.title, user)
        if not task_id:
            return None, clarify, msg

        update_data = {}
        if entities.description:
            update_data["description"] = entities.description
        if entities.priority:
            prio = self.entity_resolver.resolve_priority(entities.priority)
            if prio: update_data["priority"] = prio
        if entities.status:
            stat = self.entity_resolver.resolve_status(entities.status)
            if stat: update_data["status"] = stat
        if entities.due_date:
            dt = self.entity_resolver.resolve_date(entities.due_date)
            if dt: update_data["due_date"] = dt

        if not update_data:
            return None, True, "What exactly would you like to update?"

        task_in = TaskUpdate(**update_data)
        updated = await self.task_service.update_task(task_id, user, task_in)

        if not updated:
            return AIActionResult(action_type=IntentType.UPDATE_TASK, success=False), False, "Failed to update the task."

        return AIActionResult(action_type=IntentType.UPDATE_TASK, success=True, data={"task_id": str(updated.id)}), False, f"Updated task '{updated.title}'."

    async def _handle_complete_task(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        task_id, msg, clarify = await self._resolve_target_task(entities.task_name or entities.title, user)
        if not task_id:
            return None, clarify, msg

        updated = await self.task_service.change_status(task_id, user, "COMPLETED")
        if not updated:
            return AIActionResult(action_type=IntentType.COMPLETE_TASK, success=False), False, "Failed to complete the task."

        return AIActionResult(action_type=IntentType.COMPLETE_TASK, success=True, data={"task_id": str(updated.id)}), False, f"Marked task '{updated.title}' as complete."

    async def _handle_change_status(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        task_id, msg, clarify = await self._resolve_target_task(entities.task_name or entities.title, user)
        if not task_id:
            return None, clarify, msg

        if not entities.status:
            return None, True, "What status should I set it to?"

        status = self.entity_resolver.resolve_status(entities.status)
        if not status:
            return None, True, f"I don't recognize the status '{entities.status}'."

        updated = await self.task_service.change_status(task_id, user, status)
        if not updated:
            return AIActionResult(action_type=IntentType.CHANGE_TASK_STATUS, success=False), False, "Failed to change task status."

        return AIActionResult(action_type=IntentType.CHANGE_TASK_STATUS, success=True, data={"task_id": str(updated.id)}), False, f"Changed status to {status} for '{updated.title}'."

    async def _handle_change_priority(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        task_id, msg, clarify = await self._resolve_target_task(entities.task_name or entities.title, user)
        if not task_id:
            return None, clarify, msg

        if not entities.priority:
            return None, True, "What priority should I set?"

        priority = self.entity_resolver.resolve_priority(entities.priority)
        if not priority:
            return None, True, f"I don't recognize the priority '{entities.priority}'."

        updated = await self.task_service.change_priority(task_id, user, priority)
        if not updated:
            return AIActionResult(action_type=IntentType.CHANGE_TASK_PRIORITY, success=False), False, "Failed to change task priority."

        return AIActionResult(action_type=IntentType.CHANGE_TASK_PRIORITY, success=True, data={"task_id": str(updated.id)}), False, f"Changed priority to {priority} for '{updated.title}'."

    async def _handle_search_tasks(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        project_id = None
        if entities.project_name:
            res = await self.entity_resolver.resolve_project(entities.project_name, user)
            if res.status == ResolutionStatus.MATCHED:
                project_id = res.entity_id

        items, total = await self.task_service.list_tasks(
            user=user,
            skip=0,
            limit=10,
            project_id=project_id,
            client_id=None,
            status=self.entity_resolver.resolve_status(entities.status) if entities.status else None,
            priority=self.entity_resolver.resolve_priority(entities.priority) if entities.priority else None,
            search=entities.search_query or entities.title
        )

        data = {"count": total, "tasks": [{"id": str(t.id), "title": t.title} for t in items]}
        return AIActionResult(action_type=IntentType.SEARCH_TASKS, success=True, data=data), False, f"I found {total} tasks matching your search."

    async def _handle_get_today_tasks(
        self, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        dash = await self.dashboard_service.get_today_dashboard(user)
        today_tasks = dash.get("due_today", [])
        data = {"count": len(today_tasks), "tasks": [{"id": str(t["id"]), "title": t["title"]} for t in today_tasks]}
        return AIActionResult(action_type=IntentType.GET_TODAY_TASKS, success=True, data=data), False, f"You have {len(today_tasks)} tasks due today."

    async def _handle_get_overdue_tasks(
        self, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        dash = await self.dashboard_service.get_today_dashboard(user)
        overdue_tasks = dash.get("overdue", [])
        data = {"count": len(overdue_tasks), "tasks": [{"id": str(t["id"]), "title": t["title"]} for t in overdue_tasks]}
        return AIActionResult(action_type=IntentType.GET_OVERDUE_TASKS, success=True, data=data), False, f"You have {len(overdue_tasks)} overdue tasks."

    async def _handle_get_project_info(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        if not entities.project_name:
            return None, True, "Which project do you want info about?"

        res = await self.entity_resolver.resolve_project(entities.project_name, user)
        if res.status == ResolutionStatus.AMBIGUOUS:
            return None, True, f"Which project? Options: {', '.join([c['name'] for c in res.candidates])}"
        elif res.status == ResolutionStatus.NOT_FOUND:
            return None, True, f"I couldn't find project '{entities.project_name}'."

        project = await self.project_service.get_project(res.entity_id, user)
        if not project:
            return AIActionResult(action_type=IntentType.GET_PROJECT_INFO, success=False), False, "Failed to retrieve project info."

        data = {"id": str(project.id), "name": project.name, "description": project.description}
        return AIActionResult(action_type=IntentType.GET_PROJECT_INFO, success=True, data=data), False, f"Project '{project.name}': {project.description or 'No description provided.'}"

    async def _handle_get_client_info(
        self, entities: ExtractedEntities, user: User
    ) -> Tuple[Optional[AIActionResult], bool, Optional[str]]:
        if not entities.client_name:
            return None, True, "Which client do you want info about?"

        res = await self.entity_resolver.resolve_client(entities.client_name, user)
        if res.status == ResolutionStatus.AMBIGUOUS:
            return None, True, f"Which client? Options: {', '.join([c['name'] for c in res.candidates])}"
        elif res.status == ResolutionStatus.NOT_FOUND:
            return None, True, f"I couldn't find client '{entities.client_name}'."

        client = await self.client_service.get_client(res.entity_id, user)
        if not client:
            return AIActionResult(action_type=IntentType.GET_CLIENT_INFO, success=False), False, "Failed to retrieve client info."

        data = {"id": str(client.id), "name": client.name}
        return AIActionResult(action_type=IntentType.GET_CLIENT_INFO, success=True, data=data), False, f"Found client '{client.name}'."
