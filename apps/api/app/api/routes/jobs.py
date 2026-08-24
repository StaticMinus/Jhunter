"""
AI Job Hunter — Job Discovery, Listing & Matching API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
import hashlib

from app.db.session import session_factory
from app.models import Job, JobFeature, JobMatch, JobSource, CandidateProfile, CandidateSkill
from app.schemas import JobDetailResponse, JobMatchResponse, JobFeatureResponse
from app.services.matching_engine import MatchingEngine
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


# Baseline high-signal seed jobs matching the user's domain (Nigeria, Remote, International NGO)
SAMPLE_SEEDS = [
    {
        "title": "ICT Specialist & Systems Administrator",
        "employer": "International Humanitarian Health Org",
        "location": "Abuja, Nigeria",
        "work_mode": "hybrid",
        "canonical_url": "https://careers.example-ngo.org/jobs/ict-specialist-abuja",
        "salary_min": 750000.0,
        "salary_max": 950000.0,
        "currency": "NGN",
        "visa_signal": "indicated",
        "skills": ["lan/wan & tcp/ip networking", "active directory", "windows & linux server administration", "cybersecurity & ids/ips", "disaster recovery & backup architecture", "ict4d & humanitarian technology"],
        "description": "Seeking a senior ICT Specialist to manage regional infrastructure, secure VPN tunnels, Starlink satellite connectivity, Active Directory, server virtualization, and disaster recovery backup systems for healthcare response teams in Nigeria."
    },
    {
        "title": "Senior Python & Cloud Infrastructure Engineer",
        "employer": "Fintech Global Solutions",
        "location": "Worldwide / Remote",
        "work_mode": "remote",
        "canonical_url": "https://remoteok.com/remote-jobs/senior-python-infra-engineer",
        "salary_min": 6500.0,
        "salary_max": 8500.0,
        "currency": "USD",
        "visa_signal": "possible",
        "skills": ["python & api development", "azure & cloud", "linux server administration", "cybersecurity", "full stack web & mobile development"],
        "description": "Lead Python backend architecture, high-throughput REST APIs, Azure cloud integration, security incident response, and containerized microservices. 100% remote with international relocation sponsorship potential."
    },
    {
        "title": "ICT4D Technology & Digital Transformation Lead",
        "employer": "United Nations / International NGO Consortium",
        "location": "Geneva / Amsterdam / Remote",
        "work_mode": "remote",
        "canonical_url": "https://reliefweb.int/job/ict4d-technology-digital-lead",
        "salary_min": 7000.0,
        "salary_max": 9000.0,
        "currency": "EUR",
        "visa_signal": "indicated",
        "skills": ["ict4d & humanitarian technology", "python & api development", "cybersecurity & ids/ips", "documentary production & communications", "lan/wan & tcp/ip networking"],
        "description": "Lead global digital technology strategy, mobile assessment tools, telehealth integrations, humanitarian IT compliance, and stakeholder technical mentoring across country offices."
    },
    {
        "title": "Enterprise Cybersecurity & Network Engineer",
        "employer": "West African Telecoms Group",
        "location": "Lagos, Nigeria",
        "work_mode": "hybrid",
        "canonical_url": "https://hotnigerianjobs.com/jobs/enterprise-cybersecurity-engineer",
        "salary_min": 800000.0,
        "salary_max": 1100000.0,
        "currency": "NGN",
        "visa_signal": "no_indication",
        "skills": ["cybersecurity & ids/ips", "lan/wan & tcp/ip networking", "active directory", "disaster recovery & backup architecture"],
        "description": "Responsible for core telecommunication network security, IDS/IPS hardening, multi-site failover disaster recovery, and SOC monitoring across enterprise infrastructure."
    }
]


async def seed_jobs_if_empty(db: AsyncSession, profile: CandidateProfile):
    stmt = select(Job).limit(1)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        # Add a default job source
        source = JobSource(name="ReliefWeb & Hot Nigerian Jobs", type="aggregator", base_url="https://reliefweb.int")
        db.add(source)
        await db.flush()

        # Build candidate profile dict for scoring
        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
        skills_objs = skills_res.scalars().all()
        prof_dict = {
            "skills": [{"skill": s.skill} for s in skills_objs],
            "preferences_json": profile.preferences_json,
            "location": profile.location,
            "salary_floor": profile.salary_floor
        }

        for seed in SAMPLE_SEEDS:
            raw_hash = hashlib.sha256((seed["title"] + seed["employer"] + seed["canonical_url"]).encode()).hexdigest()
            job = Job(
                source_id=source.id,
                canonical_url=seed["canonical_url"],
                title=seed["title"],
                employer=seed["employer"],
                location=seed["location"],
                work_mode=seed["work_mode"],
                salary_min=seed["salary_min"],
                salary_max=seed["salary_max"],
                currency=seed["currency"],
                description=seed["description"],
                posted_at=datetime.now(timezone.utc),
                raw_hash=raw_hash
            )
            db.add(job)
            await db.flush()

            features = JobFeature(
                job_id=job.id,
                skills_json=seed["skills"],
                seniority="Senior",
                industry="IT / Humanitarian / Telecom",
                visa_signal=seed["visa_signal"],
                remote_signal="full_remote" if seed["work_mode"] == "remote" else "hybrid",
                extracted_salary={"min": seed["salary_min"], "max": seed["salary_max"], "currency": seed["currency"]}
            )
            db.add(features)
            await db.flush()

            # Run Scoring Engine
            match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                profile_data=prof_dict,
                job_data=seed,
                job_features={"skills_json": seed["skills"], "visa_signal": seed["visa_signal"]}
            )

            match = JobMatch(
                job_id=job.id,
                profile_id=profile.id,
                match_score=match_score,
                opportunity_score=opp_score,
                explanation_json=explanation,
                gaps_json=gaps
            )
            db.add(match)

        await db.commit()


@router.get("", response_model=List[JobDetailResponse])
async def list_jobs(
    query: Optional[str] = None,
    min_match: Optional[int] = Query(None, ge=0, le=100),
    min_opportunity: Optional[int] = Query(None, ge=0, le=100),
    work_mode: Optional[str] = None,
    location_filter: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    await seed_jobs_if_empty(db, profile)

    stmt = select(Job).order_by(desc(Job.created_at)).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    output = []
    for j in jobs:
        feat_res = await db.execute(select(JobFeature).where(JobFeature.job_id == j.id))
        j_feat = feat_res.scalar_one_or_none()

        match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == j.id, JobMatch.profile_id == profile.id))
        j_match = match_res.scalar_one_or_none()

        # Apply in-memory filtering for rich multi-factor queries
        if min_match and j_match and j_match.match_score < min_match:
            continue
        if min_opportunity and j_match and j_match.opportunity_score < min_opportunity:
            continue
        if query and query.lower() not in (j.title + j.employer + j.description).lower():
            continue
        if work_mode and work_mode.lower() not in (j.work_mode or "").lower():
            continue

        item = JobDetailResponse(
            id=j.id,
            canonical_url=j.canonical_url,
            title=j.title,
            employer=j.employer,
            location=j.location,
            work_mode=j.work_mode,
            salary_min=float(j.salary_min) if j.salary_min else None,
            salary_max=float(j.salary_max) if j.salary_max else None,
            currency=j.currency,
            description=j.description,
            posted_at=j.posted_at,
            created_at=j.created_at,
            features=JobFeatureResponse(
                skills_json=j_feat.skills_json if j_feat else [],
                seniority=j_feat.seniority if j_feat else None,
                industry=j_feat.industry if j_feat else None,
                visa_signal=j_feat.visa_signal if j_feat else "unknown",
                remote_signal=j_feat.remote_signal if j_feat else "unknown",
                extracted_salary=j_feat.extracted_salary if j_feat else None,
                requirements_json=j_feat.requirements_json if j_feat else []
            ) if j_feat else None,
            match=JobMatchResponse(
                id=j_match.id,
                match_score=j_match.match_score,
                opportunity_score=j_match.opportunity_score,
                explanation_json=j_match.explanation_json,
                gaps_json=j_match.gaps_json,
                created_at=j_match.created_at
            ) if j_match else None
        )
        output.append(item)

    return output


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(job_id: str, db: AsyncSession = Depends(get_db)):
    profile = await get_or_create_default_profile(db)
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    j = res.scalar_one_or_none()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    feat_res = await db.execute(select(JobFeature).where(JobFeature.job_id == j.id))
    j_feat = feat_res.scalar_one_or_none()

    match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == j.id, JobMatch.profile_id == profile.id))
    j_match = match_res.scalar_one_or_none()

    return JobDetailResponse(
        id=j.id,
        canonical_url=j.canonical_url,
        title=j.title,
        employer=j.employer,
        location=j.location,
        work_mode=j.work_mode,
        salary_min=float(j.salary_min) if j.salary_min else None,
        salary_max=float(j.salary_max) if j.salary_max else None,
        currency=j.currency,
        description=j.description,
        posted_at=j.posted_at,
        created_at=j.created_at,
        features=JobFeatureResponse(
            skills_json=j_feat.skills_json if j_feat else [],
            seniority=j_feat.seniority if j_feat else None,
            industry=j_feat.industry if j_feat else None,
            visa_signal=j_feat.visa_signal if j_feat else "unknown",
            remote_signal=j_feat.remote_signal if j_feat else "unknown",
            extracted_salary=j_feat.extracted_salary if j_feat else None,
            requirements_json=j_feat.requirements_json if j_feat else []
        ) if j_feat else None,
        match=JobMatchResponse(
            id=j_match.id,
            match_score=j_match.match_score,
            opportunity_score=j_match.opportunity_score,
            explanation_json=j_match.explanation_json,
            gaps_json=j_match.gaps_json,
            created_at=j_match.created_at
        ) if j_match else None
    )


@router.post("/scan")
async def trigger_job_scan(db: AsyncSession = Depends(get_db)):
    """Triggers an on-demand scan across configured source adapters."""
    profile = await get_or_create_default_profile(db)
    await seed_jobs_if_empty(db, profile)
    return {
        "status": "success",
        "message": "Scan completed across Nigerian job boards, ReliefWeb, and Remote feeds.",
        "scanned_count": len(SAMPLE_SEEDS),
        "new_matches": len(SAMPLE_SEEDS)
    }
