from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TaskLabelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, max_length=7)

class TaskLabelResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str | None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
