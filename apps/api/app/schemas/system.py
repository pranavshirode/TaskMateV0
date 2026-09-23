from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    name: str
    version: str
    environment: str
