"""Pydantic schemas for GitHub resources."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class GitHubUser(BaseModel):
    id: int
    login: str
    avatar_url: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: Optional[str] = None
    default_branch: str


class GitHubIssue(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    body: Optional[str] = None
    user: GitHubUser


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    body: Optional[str] = None
    user: GitHubUser
    merged: Optional[bool] = None

