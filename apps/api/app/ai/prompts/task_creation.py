"""Task creation prompt — task_creation_v1.

Extracts structured task data from natural language for task creation.
"""

from app.ai.prompts.base import PromptTemplate

TASK_CREATION_PROMPT = PromptTemplate(
    name="task_creation",
    version="v1",
    description="Extract task creation parameters from natural language",
    template="""Extract task details from the user's message for creating a new task.

Available projects: {available_projects}
Available clients: {available_clients}
Current date: {current_date}

User message: "{user_message}"

Extract and return JSON:
{{
  "title": "<clear, concise task title>",
  "description": "<task description if mentioned, or null>",
  "project_name": "<matching project name from available list, or null>",
  "client_name": "<matching client name from available list, or null>",
  "priority": "<LOW|MEDIUM|HIGH|URGENT — default MEDIUM if not specified>",
  "due_date": "<date expression or null>",
  "estimated_minutes": <integer or null>
}}

Rules:
- Match project/client names against the available lists. Use the closest match.
- If no project/client is mentioned, set to null.
- Infer priority from words like "urgent", "important", "high priority", "low priority".
- Convert relative dates: "tomorrow", "next Monday", "Friday", "end of week", etc.
- Create a clean, actionable task title even if the user's phrasing is informal.""",
)
