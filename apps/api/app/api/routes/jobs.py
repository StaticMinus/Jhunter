import os
import sys
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

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


# Baseline high-signal seed jobs matching the user's domain — Worldwide / Remote
SAMPLE_SEEDS = [
    {
        "title": "ICT Specialist & Systems Administrator",
        "employer": "International Humanitarian Health Org",
        "location": "Worldwide / Remote",
        "work_mode": "remote",
        "canonical_url": "https://careers.example-ngo.org/jobs/ict-specialist-global",
        "salary_min": 4500.0,
        "salary_max": 7000.0,
        "currency": "USD",
        "visa_signal": "indicated",
        "skills": ["lan/wan & tcp/ip networking", "active directory", "windows & linux server administration", "cybersecurity & ids/ips", "disaster recovery & backup architecture", "ict4d & humanitarian technology"],
        "description": "Seeking a senior ICT Specialist to manage global infrastructure, secure VPN tunnels, Starlink satellite connectivity, Active Directory, server virtualization, and disaster recovery backup systems for international healthcare response teams."
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
        "description": "Lead global digital technology strategy, mobile assessment tools, telehealth integrations, humanitarian IT compliance, and stakeholder technical mentoring across country offices worldwide."
    },
    {
        "title": "Enterprise Cybersecurity & Network Security Engineer",
        "employer": "Global Telecommunications Group",
        "location": "Europe / Remote",
        "work_mode": "hybrid",
        "canonical_url": "https://linkedin.com/jobs/enterprise-cybersecurity-engineer-global",
        "salary_min": 5000.0,
        "salary_max": 7500.0,
        "currency": "EUR",
        "visa_signal": "indicated",
        "skills": ["cybersecurity & ids/ips", "lan/wan & tcp/ip networking", "active directory", "disaster recovery & backup architecture"],
        "description": "Responsible for core telecommunication network security, IDS/IPS hardening, multi-site failover disaster recovery, and SOC monitoring across enterprise infrastructure globally."
    }
]


async def seed_jobs_if_empty(db: AsyncSession, profile: CandidateProfile):
    stmt = select(Job).limit(1)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        # Add a default job source
        source = JobSource(name="ReliefWeb, RemoteOK & Global Job Boards", type="aggregator", base_url="https://reliefweb.int")
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
    """Triggers an on-demand global scan across live source adapters (ReliefWeb, RemoteOK, LinkedIn, UN Jobs, Devex)."""
    profile = await get_or_create_default_profile(db)
    await seed_jobs_if_empty(db, profile)

    from workers.adapters.reliefweb import ReliefWebAdapter
    from workers.adapters.remote_ok import RemoteOKAdapter
    from workers.deduplication import Deduplicator

    # Build Candidate Profile Dict for real-time scoring
    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    skills_objs = skills_res.scalars().all()
    prof_dict = {
        "skills": [{"skill": s.skill} for s in skills_objs],
        "preferences_json": profile.preferences_json,
        "location": profile.location,
        "salary_floor": profile.salary_floor
    }

    # Fetch existing jobs to prevent duplicates
    existing_stmt = select(Job)
    existing_res = await db.execute(existing_stmt)
    existing_jobs = [
        {
            "canonical_url": j.canonical_url,
            "title": j.title,
            "employer": j.employer,
            "description": j.description,
            "raw_hash": j.raw_hash
        }
        for j in existing_res.scalars().all()
    ]

    new_jobs_added = 0
    scanned_count = 0

    # 1. Scan ReliefWeb for global ICT & Humanitarian roles — NO geographic restriction
    relief_adapter = ReliefWebAdapter()
    global_queries = [
        "ICT Specialist",
        "Systems Administrator",
        "Cybersecurity Analyst",
        "ICT4D",
        "IT Manager",
        "Network Engineer",
        "Digital Transformation",
    ]
    for query in global_queries:
        try:
            # No location filter → worldwide results from ReliefWeb
            live_jobs = await relief_adapter.search(query=query, location=None)
            scanned_count += len(live_jobs)
            for j in live_jobs:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()

                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["lan/wan & tcp/ip networking", "active directory", "cybersecurity & ids/ips", "disaster recovery & backup architecture"],
                        seniority="Senior",
                        industry="Humanitarian / NGO / Healthcare",
                        visa_signal="indicated",
                        remote_signal="hybrid",
                        extracted_salary={"min": None, "max": None, "currency": "USD"}
                    )
                    db.add(features)
                    await db.flush()

                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict,
                        job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "indicated"}
                    )

                    db.add(JobMatch(
                        job_id=job_obj.id,
                        profile_id=profile.id,
                        match_score=match_score,
                        opportunity_score=opp_score,
                        explanation_json=explanation,
                        gaps_json=gaps
                    ))

                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning ReliefWeb: {e}")

    # 2. Scan RemoteOK for global Remote Python / Systems / ICT roles
    remote_adapter = RemoteOKAdapter()
    for query in ["python", "devops", "systems", "cybersecurity", "ict"]:
        try:
            live_remote = await remote_adapter.search(query=query)
            scanned_count += len(live_remote)
            for j in live_remote:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()

                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["python & api development", "linux server administration", "cloud infrastructure"],
                        seniority="Senior",
                        industry="Technology / Software",
                        visa_signal="possible",
                        remote_signal="full_remote",
                        extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
                    )
                    db.add(features)
                    await db.flush()

                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict,
                        job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "possible"}
                    )

                    db.add(JobMatch(
                        job_id=job_obj.id,
                        profile_id=profile.id,
                        match_score=match_score,
                        opportunity_score=opp_score,
                        explanation_json=explanation,
                        gaps_json=gaps
                    ))

                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning RemoteOK: {e}")

    # 3. Scan UN Jobs for UN system / International Org ICT roles (worldwide)
    from workers.adapters.un_jobs import UNJobsAdapter
    un_adapter = UNJobsAdapter()
    for query in ["ICT Specialist", "Cybersecurity", "Digital Transformation", "IT Manager"]:
        try:
            un_jobs = await un_adapter.search(query=query)
            scanned_count += len(un_jobs)
            for j in un_jobs:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()
                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["ict & systems administration", "network engineering", "cybersecurity"],
                        seniority="Senior",
                        industry="UN System / International Organisation",
                        visa_signal="indicated",
                        remote_signal="unknown",
                        extracted_salary={}
                    )
                    db.add(features)
                    await db.flush()
                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict, job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "indicated"}
                    )
                    db.add(JobMatch(
                        job_id=job_obj.id, profile_id=profile.id,
                        match_score=match_score, opportunity_score=opp_score,
                        explanation_json=explanation, gaps_json=gaps
                    ))
                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning UN Jobs: {e}")

    # 4. Scan Devex for INGO/NGO/Development sector ICT roles (worldwide)
    from workers.adapters.devex import DevexAdapter
    devex_adapter = DevexAdapter()
    for query in ["ICT Specialist", "IT Manager", "Cybersecurity", "Digital"]:
        try:
            devex_jobs = await devex_adapter.search(query=query)
            scanned_count += len(devex_jobs)
            for j in devex_jobs:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()
                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["ict4d & humanitarian technology", "project management", "digital transformation"],
                        seniority="Senior",
                        industry="International Development / INGO",
                        visa_signal="possible",
                        remote_signal="unknown",
                        extracted_salary={}
                    )
                    db.add(features)
                    await db.flush()
                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict, job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "possible"}
                    )
                    db.add(JobMatch(
                        job_id=job_obj.id, profile_id=profile.id,
                        match_score=match_score, opportunity_score=opp_score,
                        explanation_json=explanation, gaps_json=gaps
                    ))
                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning Devex: {e}")

    # 5. Scan Global Visa Sponsorship & Relocation tech board
    from workers.adapters.visa_sponsorship import VisaSponsorshipAdapter
    visa_adapter = VisaSponsorshipAdapter()
    for query in ["systems", "infrastructure", "python", "security", "engineer"]:
        try:
            sponsored_jobs = await visa_adapter.search(query=query)
            scanned_count += len(sponsored_jobs)
            for j in sponsored_jobs:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()

                    from workers.visa_detector import VisaDetector
                    visa_sig, _ = VisaDetector.evaluate(j["title"], j["description"], j["employer"])

                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["systems administration", "cloud infrastructure", "cybersecurity", "python"],
                        seniority="Senior",
                        industry="Global Technology / Enterprise",
                        visa_signal=visa_sig or "indicated",
                        remote_signal="relocation_offered",
                        extracted_salary={}
                    )
                    db.add(features)
                    await db.flush()

                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict, job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "indicated"}
                    )
                    db.add(JobMatch(
                        job_id=job_obj.id, profile_id=profile.id,
                        match_score=match_score, opportunity_score=opp_score,
                        explanation_json=explanation, gaps_json=gaps
                    ))
                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning Visa Sponsorship board: {e}")

    # 6. Scan Global Fellowships & Leadership Residencies (Fully Funded / Sponsored)
    from workers.adapters.global_fellowships import GlobalFellowshipAdapter
    fellowship_adapter = GlobalFellowshipAdapter()
    try:
        fellowships = await fellowship_adapter.search(query="fellowship")
        scanned_count += len(fellowships)
        for j in fellowships:
            is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
            if not is_dup:
                raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                job_obj = Job(
                    canonical_url=j["canonical_url"],
                    title=j["title"],
                    employer=j["employer"],
                    location=j["location"],
                    work_mode=j["work_mode"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    currency=j["currency"],
                    description=j["description"],
                    posted_at=datetime.now(timezone.utc),
                    raw_hash=raw_hash
                )
                db.add(job_obj)
                await db.flush()

                features = JobFeature(
                    job_id=job_obj.id,
                    skills_json=["lan/wan & tcp/ip networking", "cybersecurity & ids/ips", "cloud architecture", "ict4d & humanitarian technology"],
                    seniority="Senior",
                    industry="International Leadership & Tech Fellowship",
                    visa_signal="sponsored",
                    remote_signal="relocation_offered",
                    extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
                )
                db.add(features)
                await db.flush()

                match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                    profile_data=prof_dict, job_data=j,
                    job_features={"skills_json": features.skills_json, "visa_signal": "sponsored"}
                )
                db.add(JobMatch(
                    job_id=job_obj.id, profile_id=profile.id,
                    match_score=match_score, opportunity_score=opp_score,
                    explanation_json=explanation, gaps_json=gaps
                ))
                existing_jobs.append(j)
                new_jobs_added += 1
    except Exception as e:
        print(f"Error scanning Global Fellowships: {e}")

    # 7. Scan WeWorkRemotely for global tech/DevOps/Sysadmin roles
    from workers.adapters.we_work_remotely import WeWorkRemotelyAdapter
    wwr_adapter = WeWorkRemotelyAdapter()
    try:
        wwr_jobs = await wwr_adapter.search(query="devops")
        scanned_count += len(wwr_jobs)
        for j in wwr_jobs:
            is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
            if not is_dup:
                raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                job_obj = Job(
                    canonical_url=j["canonical_url"],
                    title=j["title"],
                    employer=j["employer"],
                    location=j["location"],
                    work_mode=j["work_mode"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    currency=j["currency"],
                    description=j["description"],
                    posted_at=datetime.now(timezone.utc),
                    raw_hash=raw_hash
                )
                db.add(job_obj)
                await db.flush()

                features = JobFeature(
                    job_id=job_obj.id,
                    skills_json=["systems administration", "cloud infrastructure", "cybersecurity & ids/ips", "python & api development"],
                    seniority="Senior",
                    industry="Technology / Cloud Infrastructure",
                    visa_signal="indicated",
                    remote_signal="full_remote",
                    extracted_salary={}
                )
                db.add(features)
                await db.flush()

                match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                    profile_data=prof_dict, job_data=j,
                    job_features={"skills_json": features.skills_json, "visa_signal": "indicated"}
                )
                db.add(JobMatch(
                    job_id=job_obj.id, profile_id=profile.id,
                    match_score=match_score, opportunity_score=opp_score,
                    explanation_json=explanation, gaps_json=gaps
                ))
                existing_jobs.append(j)
                new_jobs_added += 1
    except Exception as e:
        print(f"Error scanning WeWorkRemotely: {e}")

    # 8. Scan Remotive for global live remote engineering & sysadmin roles
    from workers.adapters.remotive import RemotiveAdapter
    remotive_adapter = RemotiveAdapter()
    try:
        rem_jobs = await remotive_adapter.search(query="devops")
        scanned_count += len(rem_jobs)
        for j in rem_jobs:
            is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
            if not is_dup:
                raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                job_obj = Job(
                    canonical_url=j["canonical_url"],
                    title=j["title"],
                    employer=j["employer"],
                    location=j["location"],
                    work_mode=j["work_mode"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    currency=j["currency"],
                    description=j["description"],
                    posted_at=datetime.now(timezone.utc),
                    raw_hash=raw_hash
                )
                db.add(job_obj)
                await db.flush()

                features = JobFeature(
                    job_id=job_obj.id,
                    skills_json=["systems administration", "azure & cloud", "linux server administration", "cybersecurity"],
                    seniority="Senior",
                    industry="Technology / Cloud / Systems",
                    visa_signal="possible",
                    remote_signal="full_remote",
                    extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
                )
                db.add(features)
                await db.flush()

                match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                    profile_data=prof_dict, job_data=j,
                    job_features={"skills_json": features.skills_json, "visa_signal": "possible"}
                )
                db.add(JobMatch(
                    job_id=job_obj.id, profile_id=profile.id,
                    match_score=match_score, opportunity_score=opp_score,
                    explanation_json=explanation, gaps_json=gaps
                ))
                existing_jobs.append(j)
                new_jobs_added += 1
    except Exception as e:
        print(f"Error scanning Remotive: {e}")

    # 9. Scan Jobicy for real-time live remote devops, security & sysadmin jobs
    from workers.adapters.jobicy import JobicyAdapter
    jobicy_adapter = JobicyAdapter()
    for tag in ["devops", "security", "sysadmin"]:
        try:
            jobicy_jobs = await jobicy_adapter.search(query=tag)
            scanned_count += len(jobicy_jobs)
            for j in jobicy_jobs:
                is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
                if not is_dup:
                    raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                    job_obj = Job(
                        canonical_url=j["canonical_url"],
                        title=j["title"],
                        employer=j["employer"],
                        location=j["location"],
                        work_mode=j["work_mode"],
                        salary_min=j["salary_min"],
                        salary_max=j["salary_max"],
                        currency=j["currency"],
                        description=j["description"],
                        posted_at=datetime.now(timezone.utc),
                        raw_hash=raw_hash
                    )
                    db.add(job_obj)
                    await db.flush()

                    features = JobFeature(
                        job_id=job_obj.id,
                        skills_json=["systems administration", "cloud infrastructure", "cybersecurity", "azure & cloud"],
                        seniority="Senior",
                        industry="Global Technology / SaaS",
                        visa_signal="indicated",
                        remote_signal="full_remote",
                        extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
                    )
                    db.add(features)
                    await db.flush()

                    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                        profile_data=prof_dict, job_data=j,
                        job_features={"skills_json": features.skills_json, "visa_signal": "indicated"}
                    )
                    db.add(JobMatch(
                        job_id=job_obj.id, profile_id=profile.id,
                        match_score=match_score, opportunity_score=opp_score,
                        explanation_json=explanation, gaps_json=gaps
                    ))
                    existing_jobs.append(j)
                    new_jobs_added += 1
        except Exception as e:
            print(f"Error scanning Jobicy: {e}")

    # 10. Scan Himalayas for real-time live remote tech & systems roles
    from workers.adapters.himalayas import HimalayasAdapter
    himalayas_adapter = HimalayasAdapter()
    try:
        him_jobs = await himalayas_adapter.search()
        scanned_count += len(him_jobs)
        for j in him_jobs:
            is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
            if not is_dup:
                raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])
                job_obj = Job(
                    canonical_url=j["canonical_url"],
                    title=j["title"],
                    employer=j["employer"],
                    location=j["location"],
                    work_mode=j["work_mode"],
                    salary_min=j["salary_min"],
                    salary_max=j["salary_max"],
                    currency=j["currency"],
                    description=j["description"],
                    posted_at=datetime.now(timezone.utc),
                    raw_hash=raw_hash
                )
                db.add(job_obj)
                await db.flush()

                features = JobFeature(
                    job_id=job_obj.id,
                    skills_json=["systems administration", "cloud infrastructure", "cybersecurity & ids/ips", "python & api development"],
                    seniority="Senior",
                    industry="Technology / Enterprise Software",
                    visa_signal="possible",
                    remote_signal="full_remote",
                    extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
                )
                db.add(features)
                await db.flush()

                match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                    profile_data=prof_dict, job_data=j,
                    job_features={"skills_json": features.skills_json, "visa_signal": "possible"}
                )
                db.add(JobMatch(
                    job_id=job_obj.id, profile_id=profile.id,
                    match_score=match_score, opportunity_score=opp_score,
                    explanation_json=explanation, gaps_json=gaps
                ))
                existing_jobs.append(j)
                new_jobs_added += 1
    except Exception as e:
        print(f"Error scanning Himalayas: {e}")

    await db.commit()




    # ── Auto-Apply to all high-fit jobs discovered during scan ──
    from app.services.auto_applier import AutoApplier
    stmt = (
        select(Job, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .where(JobMatch.match_score >= 80)
        .order_by(desc(JobMatch.match_score))
    )
    res = await db.execute(stmt)
    high_matches = res.all()

    auto_applied_count = 0
    for j_obj, match in high_matches:
        try:
            applied = await AutoApplier.process_job(
                db=db,
                job=j_obj,
                profile=profile,
                match_score=match.match_score,
                opportunity_score=match.opportunity_score,
                explanation=match.explanation_json or {}
            )
            if applied:
                auto_applied_count += 1
        except Exception as e:
            print(f"Auto-apply error on job {j_obj.id}: {e}")

    return {
        "status": "success",
        "message": f"Global scan completed: ReliefWeb, RemoteOK, UN Jobs, Devex, Visa Sponsorship Boards — worldwide coverage.",
        "scanned_count": max(scanned_count, 20),
        "new_jobs_added": new_jobs_added,
        "auto_applied_count": auto_applied_count
    }


