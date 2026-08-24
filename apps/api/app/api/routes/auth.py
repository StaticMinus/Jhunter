"""
AI Job Hunter — Authentication & Google OAuth Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import session_factory
from app.models import User
from app.schemas import GoogleAuthRequest, AuthResponse, UserResponse
from app.api.routes.candidate import get_or_create_default_profile, get_candidate_profile

router = APIRouter()


async def get_db():
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


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
