"""Mock / Rule-based AI provider for testing, offline execution, and evaluations."""

from __future__ import annotations

import json
import re
from typing import Any

from app.ai.extractors.requirements_analyzer import analyze_brief_dynamically
from app.ai.providers.base import AIMessage, AIResponse, BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """Deterministic AI provider for testing and fallback."""

    def __init__(self, canned_response: str | None = None):
        self.canned_response = canned_response
        self.calls: list[list[AIMessage]] = []

    async def health_check(self) -> bool:
        return True

    async def generate(
        self,
        messages: list[AIMessage],
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        tools: Any = None,
        tool_choice: Any = None,
    ) -> AIResponse:
        self.calls.append(messages)

        if self.canned_response:
            return AIResponse(
                content=self.canned_response,
                model="mock-model",
                input_tokens=50,
                output_tokens=30,
                total_tokens=80,
                latency_ms=10,
            )

        # Extract system & user text
        sys_text = ""
        user_text = ""
        for m in messages:
            if m.role == "system":
                sys_text += " " + m.content
            elif m.role == "user":
                user_text = m.content

        low = user_text.lower()
        sys_low = sys_text.lower()

        # Sprint 4: Requirements Analysis prompt
        if "senior software requirements analyst" in sys_low or "analyze this client brief" in low:
            # Check for prompt injection in brief
            if any(p in low for p in ["ignore previous", "disregard all", "reveal system"]):
                analysis_data = {
                    "overview": {
                        "project_objective": "Safe Sanitized Brief",
                        "business_problem": "Detected prompt injection attempt in client brief.",
                        "intended_outcome": "Untrusted instructions were safely disregarded.",
                        "in_scope": ["Legitimate project requirements only"],
                        "out_of_scope": ["Security bypasses and instruction overrides"],
                    },
                    "functional_requirements": [
                        {
                            "key": "FR-1",
                            "title": "Enforce Input Sanitization",
                            "description": "Ensure system ignores embedded adversarial instructions.",
                            "priority": "HIGH",
                            "acceptance_criteria": [
                                "Given untrusted text, when analyzed, system policies are preserved."
                            ],
                            "dependencies": [],
                            "open_questions": [],
                        }
                    ],
                    "non_functional_requirements": [
                        {
                            "key": "NFR-1",
                            "title": "Security Guardrails",
                            "category": "SECURITY",
                            "description": "Never execute unauthorized commands.",
                            "priority": "CRITICAL",
                        }
                    ],
                    "technical_constraints": [],
                    "assumptions": [],
                    "clarification_questions": [],
                    "risks_and_dependencies": [],
                }
            else:
                analysis_data = analyze_brief_dynamically(user_text)
            return AIResponse(
                content=json.dumps(analysis_data),
                model="mock-model",
                input_tokens=150,
                output_tokens=300,
                total_tokens=450,
                latency_ms=10,
            )

        # Sprint 4: Task Planning prompt
        if "implementation planner" in sys_low or "implementation task plan" in low:
            tasks_data = {
                "proposed_tasks": [
                    {
                        "title": "Setup Architecture and Data Schema",
                        "description": "Create required models, migrations, and database tables.",
                        "priority": "HIGH",
                        "status": "TODO",
                        "deadline": None,
                        "linked_requirement_keys": ["FR-1"],
                        "acceptance_criteria": ["Database migrations execute cleanly without error."],
                        "estimated_effort": "2-3 hours",
                    },
                    {
                        "title": "Implement Backend API and Services",
                        "description": "Create service logic, repositories, and REST API endpoints.",
                        "priority": "HIGH",
                        "status": "TODO",
                        "deadline": None,
                        "linked_requirement_keys": ["FR-1", "FR-2"],
                        "acceptance_criteria": ["All unit and integration tests pass."],
                        "estimated_effort": "4-6 hours",
                    },
                    {
                        "title": "Integrate Frontend User Interface",
                        "description": "Build interactive views, forms, and responsive components.",
                        "priority": "MEDIUM",
                        "status": "TODO",
                        "deadline": None,
                        "linked_requirement_keys": ["FR-2"],
                        "acceptance_criteria": ["UI renders correctly with validation feedback."],
                        "estimated_effort": "3-5 hours",
                    },
                ],
                "rationale": "Logical three-phase execution plan moving from data layer to API to user interface.",
            }
            return AIResponse(
                content=json.dumps(tasks_data),
                model="mock-model",
                input_tokens=120,
                output_tokens=220,
                total_tokens=340,
                latency_ms=10,
            )

        # Sprint 4: Client Request Impact prompt
        if "requirements and scope impact analyst" in sys_low or "analyze the impact of this request" in low:
            impact_data = {
                "request_type": "CHANGE_REQUEST",
                "classification_explanation": "Identified client request modifying existing project requirements.",
                "affected_requirements": ["FR-1"],
                "affected_tasks": ["Implement Backend API and Services"],
                "scope_change_summary": "Extends current requirement scope to accommodate client adjustments.",
                "recommended_actions": [
                    "Review proposed change with client",
                    "Update requirement specifications upon approval",
                    "Adjust task deadlines if necessary",
                ],
            }
            return AIResponse(
                content=json.dumps(impact_data),
                model="mock-model",
                input_tokens=100,
                output_tokens=150,
                total_tokens=250,
                latency_ms=10,
            )

        # Prompt injection / security guard detection
        if any(
            pattern in low
            for pattern in [
                "ignore previous instructions",
                "disregard all previous",
                "reveal system prompt",
                "drop database",
                "delete all tables",
                "select * from",
            ]
        ):
            intent_data = {
                "intent": "GENERAL_QUESTION",
                "confidence": 0.95,
                "entities": {},
                "reasoning": "Detected prompt injection attempt or unsafe instruction; refusing unsafe action safely.",
                "reply": "I am TaskMate AI, an assistant for developer freelancers. I cannot execute database queries directly or bypass security constraints.",
            }
            return AIResponse(
                content=json.dumps(intent_data),
                model="mock-model",
                input_tokens=30,
                output_tokens=35,
                total_tokens=65,
                latency_ms=5,
            )

        # 1. Complete Task
        if re.search(r"\b(mark|set)\b.*\b(as\s+)?(complete|completed|done)\b", low) or re.search(
            r"\bcomplete\s+(the\s+)?task\b", low
        ):
            title_match = re.search(
                r"(?:mark|set)\s+(?:the\s+)?([^,]+?)\s+(?:task\s+)?(?:as\s+)?(?:complete|completed|done)", low
            )
            if not title_match:
                title_match = re.search(r"(?:complete|done)\s+(?:the\s+)?(?:task\s+)?['\"]?([^'\"\.\,]+)['\"]?", low)
            if not title_match:
                title_match = re.search(
                    r"(?:task|for)\s+['\"]?([^'\"\.\,]+)['\"]?\s+(?:as\s+)?(?:complete|completed|done)", low
                )
            ref = title_match.group(1).strip() if title_match else None
            if ref:
                ref = re.sub(r"^(the\s+)?(task\s+)?", "", ref).strip()
            intent_data = {
                "intent": "COMPLETE_TASK",
                "confidence": 0.95,
                "entities": {
                    "task_reference": ref,
                },
                "reasoning": f"User wants to mark task '{ref}' as completed",
            }

        # 2. Change Task Status
        elif (
            re.search(r"\b(move|change|set)\b.*\bstatus\b", low)
            or any(st in low for st in ["in_progress", "in progress", "blocked", "review", "backlog", "todo"])
            and any(w in low for w in ["move", "set", "mark", "change"])
        ):
            status_val = "IN_PROGRESS"
            if "blocked" in low:
                status_val = "BLOCKED"
            elif "review" in low:
                status_val = "REVIEW"
            elif "backlog" in low:
                status_val = "BACKLOG"
            elif "todo" in low or "to do" in low:
                status_val = "TODO"
            elif "complete" in low:
                status_val = "COMPLETED"

            ref_match = re.search(r"(?:task|for)\s+['\"]?([^'\"]+?)['\"]?\s+to\s+[A-Z_a-z ]+", low)
            if not ref_match:
                ref_match = re.search(r"move\s+['\"]?([^'\"]+?)['\"]?\s+to", low)
            ref = ref_match.group(1).strip() if ref_match else None

            intent_data = {
                "intent": "CHANGE_TASK_STATUS",
                "confidence": 0.92,
                "entities": {
                    "task_reference": ref,
                    "status": status_val,
                },
                "reasoning": f"Change status to {status_val}",
            }

        # 3. Change Task Priority
        elif (
            re.search(r"\b(priority|urgent|high priority|low priority)\b", low)
            and any(w in low for w in ["set", "change", "mark", "make", "raise", "lower", "reduce", "drop"])
            and not any(w in low for w in ["create", "add", "schedule"])
        ):
            prio = "HIGH"
            if "urgent" in low:
                prio = "URGENT"
            elif "low" in low:
                prio = "LOW"
            elif "medium" in low:
                prio = "MEDIUM"

            ref_match = re.search(r"(?:priority of|priority for|task)\s+['\"]?([^'\"]+?)['\"]?\s+to", low)
            ref = ref_match.group(1).strip() if ref_match else None

            intent_data = {
                "intent": "CHANGE_TASK_PRIORITY",
                "confidence": 0.92,
                "entities": {
                    "task_reference": ref,
                    "priority": prio,
                },
                "reasoning": f"Change priority to {prio}",
            }

        # 4. Create Task (check before GET_TODAY_TASKS so 'create task by today' doesn't get misclassified)
        elif any(phrase in low for phrase in ["create", "add a task", "new task", "schedule", "todo for"]):
            # Extract priority
            prio = "MEDIUM"
            if "urgent" in low:
                prio = "URGENT"
            elif "high priority" in low or "high-priority" in low:
                prio = "HIGH"
            elif "low priority" in low:
                prio = "LOW"

            # Extract due date
            due = None
            if "tomorrow" in low:
                due = "tomorrow"
            elif "today" in low:
                due = "today"
            elif "next week" in low:
                due = "next week"

            # Extract project name (e.g., "for the Acme website", "for Acme project", "in Acme")
            proj = None
            proj_match = re.search(
                r"(?:for|in)\s+(?:the\s+)?([A-Za-z0-9_\- ]+?)\s+(?:project|website|repo|app|to\b)", user_text
            )
            if not proj_match:
                proj_match = re.search(r"for\s+(?:the\s+)?([A-Za-z0-9_\-]+)\s+to", user_text)
            if proj_match:
                proj = proj_match.group(1).strip()

            # Extract title (e.g., "to fix the login bug", "task: Fix bug")
            title = None
            title_match = re.search(r"to\s+([^,\.\;]+?)(?:\s+due|\s+it needs|\s+by\s+|$)", user_text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                title_match = re.search(
                    r"task\s+(?:called|titled|named)?\s*['\"]?([^'\"]+?)['\"]?(?:\s+for|\s+due|\.|$)",
                    user_text,
                    re.IGNORECASE,
                )
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    title = user_text

            # Clean up title
            if title:
                title = re.sub(
                    r"^(create|add|schedule)\s+(an?\s+)?(urgent|high|medium|low)?\s*(priority)?\s*task\s*(for\s+.*?\s+)?(to\s+)?",
                    "",
                    title,
                    flags=re.IGNORECASE,
                ).strip()
                title = title[0].upper() + title[1:] if len(title) > 1 else title

            intent_data = {
                "intent": "CREATE_TASK",
                "confidence": 0.94,
                "entities": {
                    "task_title": title or "New Task",
                    "project_name": proj,
                    "priority": prio,
                    "due_date": due,
                },
                "reasoning": f"Create task: title={title}, project={proj}, priority={prio}, due={due}",
            }

        # 5. Today's Tasks
        elif any(
            phrase in low for phrase in ["today", "today's work", "on my plate today", "tasks for today", "due today"]
        ):
            intent_data = {
                "intent": "GET_TODAY_TASKS",
                "confidence": 0.96,
                "entities": {},
                "reasoning": "User requested tasks due today / today's dashboard",
            }

        # 6. Overdue Tasks
        elif any(phrase in low for phrase in ["overdue", "past due", "missed deadline"]):
            intent_data = {
                "intent": "GET_OVERDUE_TASKS",
                "confidence": 0.96,
                "entities": {},
                "reasoning": "User requested overdue tasks",
            }

        # 7. Search Tasks
        elif any(
            phrase in low
            for phrase in ["search", "find", "look for", "list tasks", "list all tasks", "show tasks", "filter tasks"]
        ):
            query_match = re.search(
                r"(?:search|find|look for|list|show)\s+(?:for\s+)?(?:all\s+)?(?:tasks\s+)?(?:related to\s+|about\s+|with\s+)?['\"]?([^'\"\.\?]+)['\"]?",
                user_text,
                re.IGNORECASE,
            )
            query = query_match.group(1).strip() if query_match else None
            if not query:
                query_match = re.search(
                    r"(?:search|find|for|related to)\s+['\"]?([^'\"\.\?]+)['\"]?", user_text, re.IGNORECASE
                )
                query = query_match.group(1).strip() if query_match else None
            if query:
                query = re.sub(
                    r"^(?:tasks\s+)?(?:related to\s+|about\s+|with\s+)?", "", query, flags=re.IGNORECASE
                ).strip()
            intent_data = {
                "intent": "SEARCH_TASKS",
                "confidence": 0.91,
                "entities": {
                    "search_query": query,
                },
                "reasoning": f"Search tasks with query: {query}",
            }

        # 8. Project Info
        elif any(
            phrase in low
            for phrase in ["project info", "about project", "details for project", "show project", "info about"]
        ):
            proj_match = re.search(
                r"(?:project|about)\s+['\"]?([^'\"\.\?]+?)['\"]?(?:\s+project|\?|$)", user_text, re.IGNORECASE
            )
            proj = proj_match.group(1).strip() if proj_match else None
            intent_data = {
                "intent": "GET_PROJECT_INFO",
                "confidence": 0.93,
                "entities": {
                    "project_name": proj,
                },
                "reasoning": f"Get details for project: {proj}",
            }

        # 9. Client Info
        elif any(
            phrase in low
            for phrase in [
                "client info",
                "about client",
                "details for client",
                "show client",
                "client for",
                "who is the client",
            ]
        ):
            client_match = re.search(
                r"(?:client for|client|about)\s+['\"]?([^'\"\.\?]+?)['\"]?(?:\s+client|\?|$)", user_text, re.IGNORECASE
            )
            client = client_match.group(1).strip() if client_match else None
            intent_data = {
                "intent": "GET_CLIENT_INFO",
                "confidence": 0.93,
                "entities": {
                    "client_name": client,
                },
                "reasoning": f"Get details for client: {client}",
            }

        # 10. General Question
        else:
            intent_data = {
                "intent": "GENERAL_QUESTION",
                "confidence": 0.85,
                "entities": {},
                "reasoning": "General developer question or inquiry",
                "reply": "I am your TaskMate AI assistant. How can I help you manage your projects and tasks today?",
            }

        return AIResponse(
            content=json.dumps(intent_data),
            model="mock-model",
            input_tokens=40,
            output_tokens=40,
            total_tokens=80,
            latency_ms=10,
        )
