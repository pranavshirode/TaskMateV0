"""Task update prompt — task_update_v1.

Extracts task update parameters from natural language.
"""

from app.ai.prompts.base import PromptTemplate

TASK_UPDATE_PROMPT = PromptTemplate(
    name="task_update",
    version="v1",
    description="Extract task update parameters from natural language",
    template="""Determine which task the user wants to update and what changes to make.

Available tasks: {available_tasks}
Available projects: {available_projects}
Current date: {current_date}

User message: "{user_message}"

Return JSON:
{{
  "task_name": "<name/description of task to find>",
  "updates": {{
    "title": "<new title or null>",
    "description": "<new description or null>",
    "project_name": "<new project name or null>",
    "priority": "<LOW|MEDIUM|HIGH|URGENT or null>",
    "status": "<TODO|IN_PROGRESS|REVIEW|COMPLETED or null>",
    "due_date": "<date expression or null>",
    "estimated_minutes": <integer or null>
  }}
}}

Rules:
- Identify the task from the available tasks list by name or description similarity.
- Only include fields the user explicitly wants to change.
- Use null for fields not being updated.""",
)
