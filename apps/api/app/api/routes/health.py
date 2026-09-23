from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME.lower().replace(" ", "-"),
        version=settings.APP_VERSION,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    settings = get_settings()
    service_name = settings.APP_NAME.lower().replace(" ", "-")
    try:
        await db.execute(text("SELECT 1"))
        return ReadinessResponse(
            status="ok",
            service=service_name,
            version=settings.APP_VERSION,
            checks={"database": "ok"},
        )
    except Exception:
        response.status_code = 503
        return ReadinessResponse(
            status="degraded",
            service=service_name,
            version=settings.APP_VERSION,
            checks={"database": "error: database unavailable"},
        )
