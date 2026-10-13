"""Pydantic schemas for GitHub resources."""

from datetime import datetime

from pydantic import BaseModel


class GitHubUser(BaseModel):
    id: int
    login: str
    avatar_url: str | None = None
    name: str | None = None
    email: str | None = None


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: str | None = None
    default_branch: str


class GitHubIssue(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    body: str | None = None
    user: GitHubUser


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    body: str | None = None
    user: GitHubUser
    merged: bool | None = None
