from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RepositoryProvider


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider: RepositoryProvider = RepositoryProvider.GITHUB
    url: str = Field(..., min_length=1, max_length=2000)
    default_branch: str = "main"
    description: str | None = None


class RepositoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    provider: RepositoryProvider | None = None
    url: str | None = Field(None, min_length=1, max_length=2000)
    default_branch: str | None = None
    description: str | None = None


class RepositoryResponse(BaseModel):
    id: str
    project_id: str
    name: str
    provider: RepositoryProvider
    url: str
    default_branch: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
