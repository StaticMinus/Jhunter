"""
AI Job Hunter — Multi-Candidate Profile and Pool Management Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, desc

from app.db.session import session_factory
from app.models import User, CandidateProfile, CandidateSkill, Experience, Education, Certification, Job, JobFeature, JobMatch, Application
from app.schemas import CandidateProfileResponse, CandidateProfileUpdate, CandidateSummaryResponse, CreateCandidateRequest
from app.services.cv_parser import CVParser, DAVID_DEFAULT_PROFILE
from app.services.matching_engine import MatchingEngine
from app.config import settings

router = APIRouter()


async def get_db():
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_or_create_default_profile(db: AsyncSession, profile_id: Optional[str] = None) -> CandidateProfile:
    """Helper to fetch a specific candidate profile or the primary default."""
    base_query = select(CandidateProfile).options(
        selectinload(CandidateProfile.skills),
        selectinload(CandidateProfile.experiences),
        selectinload(CandidateProfile.education),
        selectinload(CandidateProfile.certifications)
    )

    if profile_id:
        stmt = base_query.where(CandidateProfile.id == profile_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if profile:
            return profile

    target_email = getattr(settings, "default_candidate_email", "davidolagbenro35@gmail.com")
    stmt = select(User).where(User.email == target_email).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=target_email,
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
        # Re-fetch with relationships loaded
        res = await db.execute(base_query.where(CandidateProfile.id == profile.id))
        return res.scalar_one()

    # Load first candidate profile
    stmt = base_query.where(CandidateProfile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile:
        return profile

    # Fallback to any profile
    result = await db.execute(base_query.limit(1))
    return result.scalar_one()


@router.get("/candidates", response_model=List[CandidateSummaryResponse])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    """List all candidate pools with summary metrics."""
    stmt = select(CandidateProfile)
    res = await db.execute(stmt)
    profiles = res.scalars().all()

    output = []
    for p in profiles:
        user_res = await db.execute(select(User).where(User.id == p.user_id))
        u = user_res.scalar_one_or_none()

        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == p.id))
        skills = skills_res.scalars().all()

        match_cnt_res = await db.execute(select(func.count(JobMatch.id)).where(JobMatch.profile_id == p.id))
        match_cnt = match_cnt_res.scalar() or 0

        app_cnt_res = await db.execute(select(func.count(Application.id)).where(Application.profile_id == p.id))
        app_cnt = app_cnt_res.scalar() or 0

        output.append(CandidateSummaryResponse(
            id=p.id,
            user_id=p.user_id,
            name=u.name if u else "Candidate",
            email=u.email if u else "",
            seniority=p.seniority,
            location=p.location,
            target_roles=p.preferences_json.get("target_roles", []) if p.preferences_json else [],
            top_skills=[s.skill for s in skills[:5]],
            match_count=match_cnt,
            application_count=app_cnt
        ))

    return output


@router.get("/profile", response_model=CandidateProfileResponse)
async def get_candidate_profile(
    profile_id: Optional[str] = Query(None, description="Optional profile ID to view"),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
    
    return profile


@router.post("/cv", response_model=CandidateProfileResponse)
async def upload_and_parse_cv(
    file: UploadFile = File(...),
    profile_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
    content = await file.read()
    raw_text = CVParser.extract_text_from_bytes(content, file.filename or "cv.pdf")
    parsed_data = CVParser.parse_cv(raw_text)

    profile.summary = parsed_data.get("summary", profile.summary)
    profile.version += 1
    await db.commit()

    return await get_candidate_profile(profile_id=profile.id, db=db)


@router.patch("/profile", response_model=CandidateProfileResponse)
async def update_candidate_profile(
    payload: CandidateProfileUpdate,
    profile_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
    
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

    return await get_candidate_profile(profile_id=profile.id, db=db)


@router.post("/candidates/{profile_id}/match")
async def match_candidate_pool(
    profile_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Calculates and stores match scores for all existing jobs against this specific candidate profile."""
    profile_res = await db.execute(select(CandidateProfile).where(CandidateProfile.id == profile_id))
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    skills = skills_res.scalars().all()

    prof_dict = {
        "skills": [{"skill": s.skill} for s in skills],
        "preferences_json": profile.preferences_json,
        "location": profile.location,
        "salary_floor": profile.salary_floor
    }

    # Fetch all jobs in DB
    jobs_res = await db.execute(select(Job))
    all_jobs = jobs_res.scalars().all()

    matched_count = 0
    high_match_count = 0

    for job in all_jobs:
        feat_res = await db.execute(select(JobFeature).where(JobFeature.job_id == job.id))
        j_feat = feat_res.scalar_one_or_none()
        feat_dict = {
            "skills_json": j_feat.skills_json if j_feat else [],
            "visa_signal": j_feat.visa_signal if j_feat else "unknown"
        }
        job_dict = {
            "title": job.title,
            "description": job.description,
            "work_mode": job.work_mode,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency
        }

        match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
            profile_data=prof_dict,
            job_data=job_dict,
            job_features=feat_dict
        )

        # Upsert match record
        match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == job.id, JobMatch.profile_id == profile.id))
        existing_match = match_res.scalar_one_or_none()

        if existing_match:
            existing_match.match_score = match_score
            existing_match.opportunity_score = opp_score
            existing_match.explanation_json = explanation
            existing_match.gaps_json = gaps
        else:
            db.add(JobMatch(
                job_id=job.id,
                profile_id=profile.id,
                match_score=match_score,
                opportunity_score=opp_score,
                explanation_json=explanation,
                gaps_json=gaps
            ))

        matched_count += 1
        if match_score >= 80:
            high_match_count += 1

    await db.commit()

    return {
        "status": "success",
        "profile_id": profile.id,
        "jobs_matched": matched_count,
        "high_matches_found": high_match_count
    }


@router.post("/candidates", response_model=CandidateSummaryResponse)
async def create_candidate(
    payload: CreateCandidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new candidate user + profile with their skills, experience, and preferences.
    Each candidate gets scored independently against the shared job pool.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"A candidate with email {payload.email} already exists")

    # Create User
    user = User(
        email=payload.email,
        name=payload.name,
        timezone=payload.timezone,
        telegram_chat_id=payload.telegram_chat_id
    )
    db.add(user)
    await db.flush()

    # Create Profile
    profile = CandidateProfile(
        user_id=user.id,
        summary=payload.summary,
        seniority=payload.seniority,
        location=payload.location,
        salary_floor=payload.salary_floor,
        preferences_json=payload.preferences_json
    )
    db.add(profile)
    await db.flush()

    # Add Skills
    for s in payload.skills:
        db.add(CandidateSkill(
            profile_id=profile.id,
            skill=s.skill,
            category=s.category,
            proficiency=s.proficiency,
            evidence=s.evidence
        ))

    # Add Experiences
    for e in payload.experiences:
        db.add(Experience(
            profile_id=profile.id,
            employer=e.employer,
            title=e.title,
            start_date=e.start_date,
            end_date=e.end_date,
            description=e.description,
            sector=e.sector
        ))

    # Add Education
    for edu in payload.education:
        db.add(Education(
            profile_id=profile.id,
            institution=edu.institution,
            qualification=edu.qualification,
            dates=edu.dates,
            field=edu.field
        ))

    # Add Certifications
    for c in payload.certifications:
        db.add(Certification(
            profile_id=profile.id,
            name=c.name,
            issuer=c.issuer,
            year=c.year
        ))

    await db.commit()

    # Load skill names for response
    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    skills = skills_res.scalars().all()

    return CandidateSummaryResponse(
        id=profile.id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        seniority=profile.seniority,
        location=profile.location,
        target_roles=payload.preferences_json.get("target_roles", []),
        top_skills=[s.skill for s in skills[:5]],
        match_count=0,
        application_count=0
    )


@router.delete("/candidates/{profile_id}")
async def delete_candidate(
    profile_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a candidate profile and their associated user, matches, and applications."""
    profile_res = await db.execute(select(CandidateProfile).where(CandidateProfile.id == profile_id))
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    # Delete the user (cascades to profile, skills, experiences, etc.)
    user_res = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_res.scalar_one_or_none()
    if user:
        await db.delete(user)
    else:
        await db.delete(profile)

    await db.commit()
    return {"status": "deleted", "profile_id": profile_id}


@router.post("/candidates/{profile_id}/cv")
async def upload_candidate_cv(
    profile_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CV for a specific candidate. Stores the file and updates the profile's
    cv_storage_path and cv_filename so it's used in auto-apply emails.
    """
    import os
    profile_res = await db.execute(select(CandidateProfile).where(CandidateProfile.id == profile_id))
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    # Save CV file
    cv_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../cv_uploads"))
    os.makedirs(cv_dir, exist_ok=True)
    safe_filename = file.filename or f"cv_{profile_id}.pdf"
    cv_path = os.path.join(cv_dir, f"{profile_id}_{safe_filename}")

    content = await file.read()
    with open(cv_path, "wb") as f:
        f.write(content)

    # Update profile with CV path
    profile.cv_storage_path = cv_path
    profile.cv_filename = safe_filename
    db.add(profile)
    await db.commit()

    return {
        "status": "success",
        "profile_id": profile_id,
        "cv_filename": safe_filename,
        "cv_path": cv_path,
        "size_bytes": len(content)
    }

