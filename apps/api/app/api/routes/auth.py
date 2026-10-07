from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, verify_password
from app.schemas.user import User as UserSchema, UserCreate
from app.repositories.user import UserRepository
from app.api.dependencies import get_user_repository
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    user_repo: UserRepository = Depends(get_user_repository),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = await user_repo.get_by_email(email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserSchema)
async def register_user(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    user = await user_repo.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user = await user_repo.create(user_in)
    return user
