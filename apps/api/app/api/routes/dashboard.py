from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.dashboard import DashboardService
from app.schemas.dashboard import DashboardResponse

router = APIRouter()

@router.get("/today", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = DashboardService(db)
    return await service.get_today_dashboard(current_user.id)
