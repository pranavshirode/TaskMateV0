from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.system import SystemInfoResponse

router = APIRouter()


@router.get("/info", response_model=SystemInfoResponse)
async def system_info():
    settings = get_settings()
    return SystemInfoResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
