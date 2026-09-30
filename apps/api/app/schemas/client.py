from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ClientStatus

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    notes: str | None = None

class ClientUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    notes: str | None = None
    status: ClientStatus | None = None

class ClientResponse(BaseModel):
    id: str
    user_id: str
    name: str
    company_name: str | None
    email: str | None
    phone: str | None
    notes: str | None
    status: ClientStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    
    model_config = ConfigDict(from_attributes=True)
