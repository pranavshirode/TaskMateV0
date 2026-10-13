"""Agent tools for Requirements Analysis inspection."""

from __future__ import annotations

from typing import Any

from app.agent.tools.base import BaseTool, ToolResult
from app.repositories.requirements import RequirementsAnalysisRepository


class RequirementsGetAnalysisTool(BaseTool):
    name = "requirements.get_analysis"
    description = "Retrieve a requirements analysis session with its functional/non-functional requirements and questions by analysis ID."
    parameters = {
        "type": "object",
        "properties": {
            "analysis_id": {"type": "string", "description": "The requirements analysis ID"},
        },
        "required": ["analysis_id"],
    }

    async def execute(self, user_id: str, arguments: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        analysis_id = arguments.get("analysis_id")
        if not analysis_id:
            return ToolResult(success=False, error="analysis_id is required")

        db = context.get("db")
        if not db:
            return ToolResult(success=False, error="Database session not in context")

        repo = RequirementsAnalysisRepository(db)
        analysis = await repo.get_by_id_with_relations(analysis_id, user_id=user_id)
        if not analysis:
            return ToolResult(success=False, error="Requirements analysis not found")

        reqs = [
            {"key": r.key, "title": r.title, "priority": r.priority, "status": r.status.value}
            for r in analysis.requirements
        ]
        questions = [
            {"key": q.question_key, "question": q.question, "status": q.status.value, "answer": q.answer}
            for q in analysis.questions
        ]

        return ToolResult(
            success=True,
            data={
                "id": analysis.id,
                "title": analysis.title,
                "status": analysis.status.value,
                "version": analysis.version,
                "requirements": reqs,
                "questions": questions,
            },
        )


class RequirementsListProjectTool(BaseTool):
    name = "requirements.list_for_project"
    description = "List all requirements analyses for a specified project ID."
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "The project ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, user_id: str, arguments: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        project_id = arguments.get("project_id")
        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        db = context.get("db")
        if not db:
            return ToolResult(success=False, error="Database session not in context")

        repo = RequirementsAnalysisRepository(db)
        analyses = await repo.list_by_project(project_id, user_id=user_id)

        data = [
            {
                "id": a.id,
                "title": a.title,
                "status": a.status.value,
                "version": a.version,
                "total_requirements": len(a.requirements),
            }
            for a in analyses
        ]

        return ToolResult(success=True, data={"analyses": data, "count": len(data)})
