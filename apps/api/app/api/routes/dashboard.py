from typing import Any
from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.dashboard import DashboardTodayResponse
from app.services.dashboard import DashboardService
from app.api.dependencies import get_current_user, get_dashboard_service

router = APIRouter()

@router.get("/today", response_model=DashboardTodayResponse)
async def get_dashboard_today(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> Any:
    return await dashboard_service.get_today_dashboard(current_user)
