"""GitHub tools for the agent system.

These tools wrap the GitHubClient, allowing the agent
to read from GitHub via natural language.
"""

import logging
from typing import Any

from app.agent.tools.base import AgentTool, ToolContext, ToolPermission, ToolResult

logger = logging.getLogger(__name__)


class GitHubRepositoryGetTool(AgentTool):
    """Get repository metadata."""

    @property
    def name(self) -> str:
        return "github.repository.get"

    @property
    def description(self) -> str:
        return "Get details of a GitHub repository."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner (user or organization)"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            repo = await client.get_repository(input_data["owner"], input_data["repo"])
            return ToolResult.ok(repo.model_dump(mode="json"))
        except Exception as e:
            logger.exception("github.repository.get failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to get repository: {e}")


class GitHubRepositoryListTool(AgentTool):
    """List the user's GitHub repositories."""

    @property
    def name(self) -> str:
        return "github.repository.list"

    @property
    def description(self) -> str:
        return "List all repositories the authenticated user has access to."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            repos = await client.list_repositories()
            return ToolResult.ok({
                "repositories": [repo.model_dump(mode="json") for repo in repos],
                "count": len(repos),
            })
        except Exception as e:
            logger.exception("github.repository.list failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to list repositories: {e}")


class GitHubIssueGetTool(AgentTool):
    """Get a GitHub issue."""

    @property
    def name(self) -> str:
        return "github.issue.get"

    @property
    def description(self) -> str:
        return "Get details of a specific GitHub issue."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_number": {"type": "integer", "description": "Issue number"},
            },
            "required": ["owner", "repo", "issue_number"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            issue = await client.get_issue(
                input_data["owner"], input_data["repo"], input_data["issue_number"]
            )
            return ToolResult.ok(issue.model_dump(mode="json"))
        except Exception as e:
            logger.exception("github.issue.get failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to get issue: {e}")


class GitHubIssueListTool(AgentTool):
    """List GitHub issues."""

    @property
    def name(self) -> str:
        return "github.issue.list"

    @property
    def description(self) -> str:
        return "List issues for a repository. Defaults to open issues."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Issue state (default: open)",
                },
            },
            "required": ["owner", "repo"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            state = input_data.get("state", "open")
            issues = await client.list_issues(input_data["owner"], input_data["repo"], state)
            return ToolResult.ok({
                "issues": [issue.model_dump(mode="json") for issue in issues],
                "count": len(issues),
            })
        except Exception as e:
            logger.exception("github.issue.list failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to list issues: {e}")


class GitHubPullRequestGetTool(AgentTool):
    """Get a GitHub pull request."""

    @property
    def name(self) -> str:
        return "github.pull_request.get"

    @property
    def description(self) -> str:
        return "Get details of a specific GitHub pull request."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {"type": "integer", "description": "Pull request number"},
            },
            "required": ["owner", "repo", "pr_number"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            pr = await client.get_pull_request(
                input_data["owner"], input_data["repo"], input_data["pr_number"]
            )
            return ToolResult.ok(pr.model_dump(mode="json"))
        except Exception as e:
            logger.exception("github.pull_request.get failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to get PR: {e}")


class GitHubPullRequestListTool(AgentTool):
    """List GitHub pull requests."""

    @property
    def name(self) -> str:
        return "github.pull_request.list"

    @property
    def description(self) -> str:
        return "List pull requests for a repository. Defaults to open PRs."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "PR state (default: open)",
                },
            },
            "required": ["owner", "repo"],
        }

    @property
    def permission(self) -> ToolPermission:
        return ToolPermission.READ

    async def execute(self, input_data: dict[str, Any], context: ToolContext) -> ToolResult:
        github_service = context.extra.get("github_service")
        if not github_service:
            return ToolResult.fail("CONFIGURATION_ERROR", "GitHub service not available")

        try:
            client = await github_service.create_client(context.user)
            state = input_data.get("state", "open")
            prs = await client.list_pull_requests(input_data["owner"], input_data["repo"], state)
            return ToolResult.ok({
                "pull_requests": [pr.model_dump(mode="json") for pr in prs],
                "count": len(prs),
            })
        except Exception as e:
            logger.exception("github.pull_request.list failed")
            return ToolResult.fail("EXTERNAL_ERROR", f"Failed to list PRs: {e}")


def get_github_tools() -> list[AgentTool]:
    """Return all GitHub tools for registry registration."""
    return [
        GitHubRepositoryGetTool(),
        GitHubRepositoryListTool(),
        GitHubIssueGetTool(),
        GitHubIssueListTool(),
        GitHubPullRequestGetTool(),
        GitHubPullRequestListTool(),
    ]

