"""GitHub API client using httpx."""

import httpx
from typing import List, Optional

from app.integrations.github.schemas import (
    GitHubUser,
    GitHubRepository,
    GitHubIssue,
    GitHubPullRequest,
)


class GitHubClient:
    """Async client for GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_authenticated_user(self) -> GitHubUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/user", headers=self.headers
            )
            response.raise_for_status()
            return GitHubUser(**response.json())

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}", headers=self.headers
            )
            response.raise_for_status()
            return GitHubRepository(**response.json())

    async def list_repositories(self) -> List[GitHubRepository]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/user/repos?sort=updated&per_page=100",
                headers=self.headers,
            )
            response.raise_for_status()
            return [GitHubRepository(**repo) for repo in response.json()]

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> GitHubIssue:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            # If 'pull_request' is in data, it's technically a PR, but GitHub returns it as an issue too.
            return GitHubIssue(**data)

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> List[GitHubIssue]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues?state={state}&per_page=100",
                headers=self.headers,
            )
            response.raise_for_status()
            # Filter out PRs, as GitHub API returns PRs in the issues endpoint
            issues = [issue for issue in response.json() if "pull_request" not in issue]
            return [GitHubIssue(**issue) for issue in issues]

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> GitHubPullRequest:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self.headers,
            )
            response.raise_for_status()
            return GitHubPullRequest(**response.json())

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[GitHubPullRequest]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls?state={state}&per_page=100",
                headers=self.headers,
            )
            response.raise_for_status()
            return [GitHubPullRequest(**pr) for pr in response.json()]

