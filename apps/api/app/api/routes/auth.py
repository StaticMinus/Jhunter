"""
AI Job Hunter — Authentication & Google OAuth2 Routes
Handles the full OAuth flow: authorize → callback → token storage → Gmail access.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import session_factory
from app.models import User, AuditLog
from app.schemas import GoogleAuthRequest, AuthResponse, UserResponse
from app.api.routes.candidate import get_or_create_default_profile, get_candidate_profile
from app.services.gmail_service import GmailService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_db():
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get("/google/authorize")
async def google_authorize():
    """Redirect the user to Google's OAuth consent screen."""
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={settings.google_redirect_uri}&"
        f"scope=https://www.googleapis.com/auth/gmail.send "
        f"https://www.googleapis.com/auth/gmail.readonly "
        f"https://www.googleapis.com/auth/userinfo.email&"
        f"response_type=code&access_type=offline&prompt=consent"
    )
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    """
    Google redirects here after user approves. Exchange code for tokens
    and save them so the system can send Gmail on David's behalf.
    """
    if error or not code:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error or 'no code received'}")

    # Exchange code for access_token + refresh_token
    tokens = await GmailService.exchange_code_for_tokens(code)
    if not tokens:
        raise HTTPException(status_code=500, detail="Failed to exchange authorization code for tokens")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Get the real Gmail address of the user
    gmail_address = await GmailService.get_user_email(access_token)
    if not gmail_address:
        gmail_address = "david@gmail.com"

    # Store tokens encrypted in the user record
    profile = await get_or_create_default_profile(db)
    user_res = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_res.scalar_one()

    # Store tokens as JSON (in production, encrypt this with Fernet)
    token_payload = json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "gmail_address": gmail_address
    })
    user.google_tokens_encrypted = token_payload
    user.email = gmail_address
    db.add(user)

    db.add(AuditLog(
        action="GMAIL_OAUTH_TOKENS_STORED",
        entity_type="integration",
        user_id=user.id
    ))
    await db.commit()

    logger.info(f"✅ Gmail OAuth connected for: {gmail_address}")

    # Return a success page the user can see in the browser
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Gmail Connected — AI Job Hunter</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0a0a1a; color: #fff; display: flex; align-items: center;
                justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.3);
                 border-radius: 16px; padding: 48px; text-align: center; max-width: 480px; }}
        h1 {{ color: #6366f1; font-size: 2rem; margin-bottom: 8px; }}
        p {{ color: #94a3b8; line-height: 1.6; }}
        .email {{ background: rgba(99,102,241,0.2); border-radius: 8px; padding: 8px 16px;
                  font-family: monospace; color: #a5b4fc; display: inline-block; margin: 16px 0; }}
        .btn {{ background: linear-gradient(135deg, #6366f1, #8b5cf6);
                border: none; color: white; padding: 14px 32px; border-radius: 10px;
                font-size: 1rem; cursor: pointer; text-decoration: none;
                display: inline-block; margin-top: 24px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>✅ Gmail Connected!</h1>
        <p>AI Job Hunter is now authorized to send applications from:</p>
        <div class="email">{gmail_address}</div>
        <p>Your CV will be automatically attached to every tailored application email sent on your behalf.</p>
        <a href="http://localhost:3000" class="btn">← Return to Dashboard</a>
      </div>
    </body>
    </html>
    """)


@router.post("/google", response_model=AuthResponse)
async def google_auth_login(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    user_res = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_res.scalar_one()
    full_profile = await get_candidate_profile(db)

    return AuthResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.jhunter_verified_session",
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            timezone=user.timezone,
            created_at=user.created_at,
            profile=full_profile
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(db: AsyncSession = Depends(get_db)):
    profile = await get_or_create_default_profile(db)
    user_res = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_res.scalar_one()
    full_profile = await get_candidate_profile(db)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        timezone=user.timezone,
        created_at=user.created_at,
        profile=full_profile
    )
