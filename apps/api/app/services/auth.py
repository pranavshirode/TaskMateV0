from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.errors import ValidationError, AuthorizationError, NotFoundError
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, UserUpdate

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def register(self, data: UserRegister) -> UserResponse:
        # Check if email already exists
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValidationError("Email already registered")
        
        # Validate email format (basic check)
        if "@" not in data.email or "." not in data.email:
            raise ValidationError("Invalid email format")
        
        user = User(
            name=data.name,
            email=data.email.lower().strip(),
            password_hash=get_password_hash(data.password),
        )
        user = await self.user_repo.create(user)
        return UserResponse.model_validate(user)
    
    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email.lower().strip())
        if not user or not verify_password(data.password, user.password_hash):
            raise AuthorizationError("Invalid email or password")
        if not user.is_active:
            raise AuthorizationError("Account is deactivated")
        
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, token_type="bearer")
    
    async def get_current_user(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthorizationError("User not found or inactive")
        return user
    
    async def update_profile(self, user_id: str, data: UserUpdate) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if data.name is not None:
            user.name = data.name
        user = await self.user_repo.update(user)
        return UserResponse.model_validate(user)

