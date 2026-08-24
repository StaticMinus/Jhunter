"""
AI Job Hunter — Candidate Profile and CV Routes
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import session_factory
from app.models import User, CandidateProfile, CandidateSkill, Experience, Education, Certification
from app.schemas import CandidateProfileResponse, CandidateProfileUpdate
from app.services.cv_parser import CVParser, DAVID_DEFAULT_PROFILE

router = APIRouter()


async def get_db():
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_or_create_default_profile(db: AsyncSession) -> CandidateProfile:
    """Helper to ensure a default user/profile exists."""
    stmt = select(User).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email="david.hunter@example.com",
            name="David",
            timezone="Africa/Lagos"
        )
        db.add(user)
        await db.flush()

        profile = CandidateProfile(
            user_id=user.id,
            summary=DAVID_DEFAULT_PROFILE["summary"],
            seniority=DAVID_DEFAULT_PROFILE["seniority"],
            location=DAVID_DEFAULT_PROFILE["location"],
            salary_floor=DAVID_DEFAULT_PROFILE["salary_floor"],
            preferences_json=DAVID_DEFAULT_PROFILE["preferences_json"]
        )
        db.add(profile)
        await db.flush()

        for s in DAVID_DEFAULT_PROFILE["skills"]:
            db.add(CandidateSkill(profile_id=profile.id, **s))
        for e in DAVID_DEFAULT_PROFILE["experiences"]:
            db.add(Experience(profile_id=profile.id, **e))
        for edu in DAVID_DEFAULT_PROFILE["education"]:
            db.add(Education(profile_id=profile.id, **edu))
        for c in DAVID_DEFAULT_PROFILE["certifications"]:
            db.add(Certification(profile_id=profile.id, **c))
        
        await db.commit()
    else:
        stmt_p = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        res_p = await db.execute(stmt_p)
        profile = res_p.scalar_one_or_none()
        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                summary=DAVID_DEFAULT_PROFILE["summary"],
                seniority=DAVID_DEFAULT_PROFILE["seniority"],
                location=DAVID_DEFAULT_PROFILE["location"],
                salary_floor=DAVID_DEFAULT_PROFILE["salary_floor"],
                preferences_json=DAVID_DEFAULT_PROFILE["preferences_json"]
            )
            db.add(profile)
            await db.commit()

    return profile


@router.get("/profile", response_model=CandidateProfileResponse)
async def get_candidate_profile(db: AsyncSession = Depends(get_db)):
    profile = await get_or_create_default_profile(db)
    
    # Eager load child relations
    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    profile.skills = skills_res.scalars().all()

    exp_res = await db.execute(select(Experience).where(Experience.profile_id == profile.id))
    profile.experiences = exp_res.scalars().all()

    edu_res = await db.execute(select(Education).where(Education.profile_id == profile.id))
    profile.education = edu_res.scalars().all()

    cert_res = await db.execute(select(Certification).where(Certification.profile_id == profile.id))
    profile.certifications = cert_res.scalars().all()

    return profile


@router.post("/cv", response_model=CandidateProfileResponse)
async def upload_and_parse_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    content = await file.read()
    raw_text = CVParser.extract_text_from_bytes(content, file.filename or "cv.pdf")
    parsed_data = CVParser.parse_cv(raw_text)

    profile.summary = parsed_data.get("summary", profile.summary)
    profile.version += 1
    await db.commit()

    return await get_candidate_profile(db)


@router.patch("/profile", response_model=CandidateProfileResponse)
async def update_candidate_profile(
    payload: CandidateProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    
    if payload.summary is not None:
        profile.summary = payload.summary
    if payload.seniority is not None:
        profile.seniority = payload.seniority
    if payload.location is not None:
        profile.location = payload.location
    if payload.salary_floor is not None:
        profile.salary_floor = payload.salary_floor
    if payload.preferences_json:
        profile.preferences_json = payload.preferences_json
    
    profile.version += 1
    await db.commit()

    return await get_candidate_profile(db)
