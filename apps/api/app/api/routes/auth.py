from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
import httpx
import urllib.parse

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse, UserUpdate
from app.services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(data)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = AuthService(db)
    return await service.update_profile(current_user.id, data)


# ─── Google OAuth ──────────────────────────────────────────────────────────

@router.get("/google")
async def google_login():
    """Redirect the browser to Google's consent screen."""
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    if not settings.GOOGLE_SIGN_IN_CLIENT_ID:
        msg = urllib.parse.quote("Google Sign-In is not configured yet on this server. Please add GOOGLE_SIGN_IN_CLIENT_ID to your environment.")
        return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)

    params = urllib.parse.urlencode({
        "client_id": settings.GOOGLE_SIGN_IN_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_SIGN_IN_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}", status_code=302)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Google auth code for a TaskMate JWT."""
    from app.core.security import create_access_token
    from app.models.user import User
    from app.repositories.user import UserRepository

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    if error:
        msg = urllib.parse.quote(f"Google sign-in was cancelled: {error}")
        return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)

    if not code:
        msg = urllib.parse.quote("No authorization code was returned from Google.")
        return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)

    if not settings.GOOGLE_SIGN_IN_CLIENT_ID or not settings.GOOGLE_SIGN_IN_CLIENT_SECRET:
        msg = urllib.parse.quote("Google Sign-In is incomplete: GOOGLE_SIGN_IN_CLIENT_SECRET is missing from .env.")
        return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)

    try:
        # 1. Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_SIGN_IN_CLIENT_ID,
                    "client_secret": settings.GOOGLE_SIGN_IN_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_SIGN_IN_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                err_detail = token_resp.text
                try:
                    err_json = token_resp.json()
                    err_detail = err_json.get("error_description") or err_json.get("error") or token_resp.text
                except Exception:
                    pass
                msg = urllib.parse.quote(f"Google token exchange failed: {err_detail}")
                return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)
            token_data = token_resp.json()

            # 2. Fetch user info from Google
            info_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data.get('access_token', '')}"},
            )
            if info_resp.status_code != 200:
                msg = urllib.parse.quote("Failed to fetch user profile from Google.")
                return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)
            google_user = info_resp.json()

        email = google_user.get("email", "").lower().strip()
        name = google_user.get("name") or email.split("@")[0]

        if not email:
            msg = urllib.parse.quote("Google account did not provide an email address.")
            return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)

        # 3. Find or create local user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if not user:
            user = User(
                name=name,
                email=email,
                password_hash="",   # No password — Google-only account
            )
            user = await user_repo.create(user)

        # 4. Issue TaskMate JWT and redirect to callback page with token
        token = create_access_token({"sub": str(user.id)})
        return RedirectResponse(
            f"{frontend_url}/auth/callback?token={token}",
            status_code=302,
        )
    except Exception as exc:
        msg = urllib.parse.quote(f"Authentication error: {str(exc)}")
        return RedirectResponse(f"{frontend_url}/auth/callback?error={msg}", status_code=302)
