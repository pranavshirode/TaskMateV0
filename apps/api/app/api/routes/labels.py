from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.task_label import TaskLabelCreate, TaskLabelResponse
from app.services.label import LabelService

router = APIRouter()


@router.get("/", response_model=List[TaskLabelResponse])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabelService(db)
    return await service.list_labels(current_user.id)


@router.post(
    "/",
    response_model=TaskLabelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_label(
    data: TaskLabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LabelService(db)
    return await service.create_label(current_user.id, data)
