from typing import Any
from fastapi import APIRouter, Depends
from app.schemas.user import User as UserSchema
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    return current_user
