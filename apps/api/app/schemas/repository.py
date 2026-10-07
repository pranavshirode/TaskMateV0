import uuid
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class RepositoryBase(BaseModel):
    name: str
    provider: str = "GITHUB"
    url: HttpUrl
    default_branch: str = "main"
    description: Optional[str] = None

class RepositoryCreate(RepositoryBase):
    project_id: uuid.UUID

class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[HttpUrl] = None
    default_branch: Optional[str] = None
    description: Optional[str] = None

class RepositoryInDBBase(RepositoryBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class Repository(RepositoryInDBBase):
    pass
