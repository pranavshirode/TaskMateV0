from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TaskEventType


class TaskEventResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    event_type: TaskEventType
    old_value: str | None
    new_value: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
