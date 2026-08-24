"""
AI Job Hunter — Notifications & Event Feed Routes
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone

from app.db.session import session_factory
from app.models import Notification, CandidateProfile
from app.schemas import NotificationResponse
from app.api.routes.candidate import get_or_create_default_profile

router = APIRouter()


async def get_db():
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    profile = await get_or_create_default_profile(db)
    
    stmt = select(Notification).where(Notification.user_id == profile.user_id).order_by(desc(Notification.sent_at))
    res = await db.execute(stmt)
    items = res.scalars().all()

    if not items:
        # Seed default event feed
        demo_notifs = [
            Notification(
                user_id=profile.user_id,
                channel="telegram",
                type="HIGH_MATCH_ALERT",
                payload_json={
                    "title": "ICT Specialist & Systems Administrator",
                    "employer": "International Humanitarian Health Org",
                    "match_score": 94,
                    "opportunity_score": 97,
                    "location": "Abuja, Nigeria"
                },
                sent_at=datetime.now(timezone.utc)
            ),
            Notification(
                user_id=profile.user_id,
                channel="gmail",
                type="RESPONSE_CLASSIFIED",
                payload_json={
                    "employer": "Fintech Global Solutions",
                    "classification": "INTERVIEW_INVITE",
                    "subject": "Invitation for Technical Interview — Senior Infrastructure Engineer"
                },
                sent_at=datetime.now(timezone.utc)
            )
        ]
        for n in demo_notifs:
            db.add(n)
        await db.commit()
        
        res = await db.execute(stmt)
        items = res.scalars().all()

    return [NotificationResponse.model_validate(n) for n in items]
