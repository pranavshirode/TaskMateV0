"""Intent detection prompt — task_understanding_v1.

Used when the system needs to classify user intent
without full context (lightweight classification).
"""

from app.ai.prompts.base import PromptTemplate

INTENT_DETECTION_PROMPT = PromptTemplate(
    name="task_understanding",
    version="v1",
    description="Classify user intent from natural language",
    template="""Classify the following user message into one of the supported intents.

Supported intents:
- GENERAL_QUESTION: Questions about the workspace, tasks, projects, or general inquiries
- CREATE_TASK: User wants to create a new task
- UPDATE_TASK: User wants to update/modify an existing task's title, description, or other fields
- COMPLETE_TASK: User wants to mark a task as done/completed
- CHANGE_TASK_STATUS: User wants to change a task's status (e.g., move to in progress, review)
- CHANGE_TASK_PRIORITY: User wants to change a task's priority (e.g., make it urgent, set to low)
- SEARCH_TASKS: User wants to search, filter, or list tasks
- GET_TODAY_TASKS: User wants to see today's tasks, what to work on, or daily overview
- GET_OVERDUE_TASKS: User wants to see overdue/late tasks
- GET_PROJECT_INFO: User wants information about a specific project or all projects
- GET_CLIENT_INFO: User wants information about a specific client or all clients

User message: "{user_message}"

Respond in JSON:
{{
  "intent": "<INTENT_TYPE>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation>"
}}""",
)
