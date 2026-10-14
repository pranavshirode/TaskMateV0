"""Per-user Google OAuth: connect, keep tokens fresh, disconnect.

The access token is what TaskMate forwards (as a Bearer token) to the Google Workspace MCP server, so each
user's agent can only ever act on that user's own Google account.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.models.google_integration import GoogleIntegration
from app.models.user import User
from app.repositories.google_integration import GoogleIntegrationRepository

logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Scopes needed by the Google Workspace MCP "core" tools TaskMate enables (Gmail, Drive, Docs, Sheets,
# Slides, Calendar). Read scopes for searching; send/create scopes are only *used* after the user
# approves the action in TaskMate.
GOOGLE_SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

STATE_PURPOSE = "google_oauth"
STATE_TTL = timedelta(minutes=10)
REFRESH_MARGIN = timedelta(seconds=60)


class GoogleIntegrationError(Exception):
    """Configuration or Google-side failure, with a message safe to show the user."""


class GoogleIntegrationService:
    # Tests replace this with an httpx.MockTransport; production uses real HTTP.
    transport: httpx.AsyncBaseTransport | None = None

    def __init__(self, repository: GoogleIntegrationRepository):
        self.repository = repository
        self.settings = get_settings()

    # ------------------------------------------------------------------ helpers
    def is_configured(self) -> bool:
        return bool(self.settings.GOOGLE_OAUTH_CLIENT_ID and self.settings.GOOGLE_OAUTH_CLIENT_SECRET)

    def _require_config(self) -> str:
        if not self.is_configured():
            raise GoogleIntegrationError(
                "Google is not configured on this server (GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET)."
            )
        key = self.settings.token_encryption_key
        if not key:
            raise GoogleIntegrationError("TOKEN_ENCRYPTION_KEY is not configured on this server.")
        return key

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=15, transport=self.transport)

    # ------------------------------------------------------------------ OAuth flow
    def authorization_url(self, user: User) -> str:
        """URL to send the browser to. `state` binds the callback to this user and expires in 10 minutes."""
        self._require_config()
        state = jwt.encode(
            {"sub": str(user.id), "purpose": STATE_PURPOSE, "exp": datetime.now(timezone.utc) + STATE_TTL},
            self.settings.SECRET_KEY,
            algorithm="HS256",
        )
        params = {
            "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": self.settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",  # needed for a refresh token
            "prompt": "consent",  # always return a refresh token, even on reconnect
            "include_granted_scopes": "true",
            "state": state,
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    def _verify_state(self, user: User, state: str) -> None:
        try:
            claims = jwt.decode(state, self.settings.SECRET_KEY, algorithms=["HS256"])
        except JWTError as e:
            raise GoogleIntegrationError("The Google sign-in link expired or is invalid. Please try again.") from e
        if claims.get("purpose") != STATE_PURPOSE or claims.get("sub") != str(user.id):
            raise GoogleIntegrationError("This Google sign-in was started by a different TaskMate account.")

    async def connect(self, user: User, code: str, state: str) -> GoogleIntegration:
        """Finish the OAuth redirect: verify state, exchange the code, store tokens encrypted."""
        key = self._require_config()
        self._verify_state(user, state)

        async with self._http() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": self.settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "redirect_uri": self.settings.GOOGLE_OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            tokens = resp.json() if resp.content else {}
            if resp.status_code != 200 or "access_token" not in tokens:
                raise GoogleIntegrationError(
                    f"Google rejected the sign-in: {tokens.get('error_description') or tokens.get('error') or resp.status_code}"
                )
            if not tokens.get("refresh_token"):
                raise GoogleIntegrationError(
                    "Google did not return a refresh token. Remove TaskMate's access in your Google account settings and connect again."
                )

            info = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"})
            email = (info.json() if info.status_code == 200 else {}).get("email")
            if not email:
                raise GoogleIntegrationError("Could not read the Google account's email address.")

        integration = await self.repository.get_by_user_id(user.id) or GoogleIntegration(user_id=str(user.id))
        integration.google_email = email
        integration.encrypted_refresh_token = encrypt_token(tokens["refresh_token"], key)
        integration.encrypted_access_token = encrypt_token(tokens["access_token"], key)
        integration.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=int(tokens.get("expires_in", 3600))
        )
        integration.scopes = tokens.get("scope")
        return await self.repository.save(integration)

    # ------------------------------------------------------------------ use
    async def get_integration(self, user: User) -> GoogleIntegration | None:
        return await self.repository.get_by_user_id(user.id)

    async def get_credentials(self, user: User) -> tuple[str, str] | None:
        """(access_token, google_email) for this user, refreshed if needed; None if not connected."""
        integration = await self.repository.get_by_user_id(user.id)
        if integration is None:
            return None
        key = self._require_config()

        expires = integration.access_token_expires_at
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)  # SQLite returns naive datetimes
        if integration.encrypted_access_token and expires and expires - REFRESH_MARGIN > datetime.now(timezone.utc):
            return decrypt_token(integration.encrypted_access_token, key), integration.google_email

        async with self._http() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": self.settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "refresh_token": decrypt_token(integration.encrypted_refresh_token, key),
                    "grant_type": "refresh_token",
                },
            )
        tokens = resp.json() if resp.content else {}
        if resp.status_code != 200 or "access_token" not in tokens:
            # invalid_grant = user revoked access or (in Testing mode) the 7-day refresh token expired.
            raise GoogleIntegrationError(
                "Google access expired or was revoked. Reconnect Google in Settings → Integrations."
            )
        integration.encrypted_access_token = encrypt_token(tokens["access_token"], key)
        integration.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=int(tokens.get("expires_in", 3600))
        )
        await self.repository.save(integration)
        return tokens["access_token"], integration.google_email

    async def disconnect(self, user: User) -> bool:
        """Revoke at Google (best effort) and delete the stored tokens."""
        integration = await self.repository.get_by_user_id(user.id)
        if integration is None:
            return False
        key = self.settings.token_encryption_key
        if key:
            try:
                async with self._http() as client:
                    await client.post(
                        REVOKE_URL, data={"token": decrypt_token(integration.encrypted_refresh_token, key)}
                    )
            except Exception:  # revocation failure must not keep tokens around
                logger.warning("Google token revocation failed; deleting stored tokens anyway")
        return await self.repository.delete_by_user_id(user.id)
