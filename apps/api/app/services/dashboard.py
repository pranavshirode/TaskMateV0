import uuid
from typing import Dict, Any
from app.repositories.dashboard import DashboardRepository
from app.models.user import User

class DashboardService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    async def get_today_dashboard(self, user: User) -> Dict[str, Any]:
        return await self.repository.get_today_data(user_id=user.id)
