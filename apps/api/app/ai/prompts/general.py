"""General assistant prompt — general_assistant_v1.

For answering workspace questions using context data.
"""

from app.ai.prompts.base import PromptTemplate

GENERAL_ASSISTANT_PROMPT = PromptTemplate(
    name="general_assistant",
    version="v1",
    description="Answer general workspace questions using context",
    template="""Answer the user's question about their TaskMate workspace using the provided context.

Workspace context:
{workspace_context}

User question: "{user_message}"

Rules:
- Answer based ONLY on the provided context data.
- If the answer requires data not in the context, say you don't have that information.
- Be concise and helpful.
- Use specific numbers and names from the context.
- NEVER fabricate data not present in the context.

Respond in JSON:
{{
  "message": "<your helpful natural language answer>"
}}""",
)
