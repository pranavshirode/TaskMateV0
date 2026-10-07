"""Task search prompt — task_search_v1.

Extracts search/filter parameters from natural language.
"""

from app.ai.prompts.base import PromptTemplate

TASK_SEARCH_PROMPT = PromptTemplate(
    name="task_search",
    version="v1",
    description="Extract task search filters from natural language",
    template="""Extract search filters from the user's task search request.

Available projects: {available_projects}
Available statuses: TODO, IN_PROGRESS, REVIEW, COMPLETED
Available priorities: LOW, MEDIUM, HIGH, URGENT

User message: "{user_message}"

Return JSON:
{{
  "search_query": "<text search terms or null>",
  "project_name": "<project to filter by or null>",
  "status": "<status filter or null>",
  "priority": "<priority filter or null>",
  "label": "<label filter or null>"
}}

Rules:
- Extract explicit and implied filters.
- "backend tasks" implies search_query="backend" or label="backend".
- "high priority" implies priority="HIGH".
- "in progress" implies status="IN_PROGRESS".
- Match project names against available projects.""",
)
