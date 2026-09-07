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
    profile_id: Optional[str] = Query(None, description="Optional profile ID to score jobs against"),
    min_match: Optional[int] = Query(None, ge=0, le=100),
    min_opportunity: Optional[int] = Query(None, ge=0, le=100),
    work_mode: Optional[str] = None,
    location_filter: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
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
async def get_job_detail(
    job_id: str,
    profile_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
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


# ── Rotating scan state for fresh discovery ──
_scan_cycle_counter = 0

# ── Rotating scan state for fresh discovery ──
_scan_cycle_counter = 0

# Rotating query groups — cycle through different search terms each scan (IT, Cloud, AI, Security, MEAL, M&E & Data)
_RELIEF_WEB_QUERIES = [
    ["ICT", "Systems Administrator", "Cybersecurity", "Cloud"],
    ["MEAL", "Monitoring and Evaluation", "M&E Officer", "Data Analyst"],
    ["AI Developer", "Software Engineer", "Python", "Cloud Engineer"],
    ["MEAL Specialist", "Information Management", "DHIS2", "Data Management"],
    ["Technology", "Digital", "Network Engineer", "Infrastructure"],
    ["Penetration Tester", "Security Engineer", "DevOps", "Solutions Architect"],
    ["Global Fellow", "Leadership Fellow", "Tech Residency", "CTO"],
    ["IT Specialist", "SysAdmin", "Azure", "Information Security"],
]

_UN_JOBS_QUERIES = [
    ["ICT", "Systems Engineer", "Cloud", "Digital"],
    ["Monitoring and Evaluation", "MEAL", "Data Specialist", "M&E"],
    ["AI Developer", "Software Engineer", "Python", "DevOps"],
    ["Information Management Officer", "Data Analyst", "DHIS2"],
    ["Cybersecurity", "Penetration Tester", "Security", "Network"],
    ["Global Fellow", "Leadership", "Technology", "CTO"],
    ["Infrastructure", "Cloud Architect", "Linux", "Sysadmin"],
    ["IT Specialist", "Information Security", "Communications", "Solutions Architect"],
]

_VISA_PAGE_ROTATIONS = [
    [1, 2, 3, 4],
    [3, 4, 5, 6],
    [5, 6, 7, 8],
    [1, 3, 5, 7],
]

_HIMALAYAS_OFFSET_ROTATIONS = [
    [0, 50],
    [50, 100],
    [100, 150],
    [0, 100],
]


@router.post("/scan")
async def trigger_job_scan(db: AsyncSession = Depends(get_db)):
    """Triggers a high-throughput global scan across live source adapters with rotating pagination."""
    global _scan_cycle_counter
    _scan_cycle_counter += 1
    cycle = _scan_cycle_counter

    import logging
    scan_logger = logging.getLogger("job_scanner")

    primary_profile = await get_or_create_default_profile(db)
    await seed_jobs_if_empty(db, primary_profile)

    # Fetch all candidate profiles in the system
    all_profiles_res = await db.execute(select(CandidateProfile))
    all_profiles = all_profiles_res.scalars().all()

    from workers.adapters.reliefweb import ReliefWebAdapter
    from workers.adapters.remote_ok import RemoteOKAdapter
    from workers.adapters.un_jobs import UNJobsAdapter
    from workers.adapters.visa_sponsorship import VisaSponsorshipAdapter
    from workers.adapters.global_fellowships import GlobalFellowshipAdapter
    from workers.adapters.we_work_remotely import WeWorkRemotelyAdapter
    from workers.adapters.remotive import RemotiveAdapter
    from workers.adapters.jobicy import JobicyAdapter
    from workers.adapters.himalayas import HimalayasAdapter
    from workers.deduplication import Deduplicator
    from workers.visa_detector import VisaDetector
    from app.services.auto_applier import AutoApplier

    # Build Candidate Profile Dicts for all candidates
    candidate_profile_dicts = []
    for prof in all_profiles:
        s_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == prof.id))
        s_objs = s_res.scalars().all()
        candidate_profile_dicts.append({
            "profile": prof,
            "dict": {
                "skills": [{"skill": s.skill} for s in s_objs],
                "preferences_json": prof.preferences_json,
                "location": prof.location,
                "salary_floor": prof.salary_floor
            }
        })

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
    all_scanned_jobs = []

    # ── Rotating pagination: pick different pages/queries per cycle ──
    visa_pages = _VISA_PAGE_ROTATIONS[cycle % len(_VISA_PAGE_ROTATIONS)]
    rw_queries = _RELIEF_WEB_QUERIES[cycle % len(_RELIEF_WEB_QUERIES)]
    un_queries = _UN_JOBS_QUERIES[cycle % len(_UN_JOBS_QUERIES)]
    him_offsets = _HIMALAYAS_OFFSET_ROTATIONS[cycle % len(_HIMALAYAS_OFFSET_ROTATIONS)]

    scan_logger.info(f"[Cycle #{cycle}] Using visa pages={visa_pages}, RW queries={rw_queries}, UN queries={un_queries}")

    # 1. Visa Sponsorship & European/Global Multi-Page (Arbeitnow rotating pages)
    visa_adapter = VisaSponsorshipAdapter()
    try:
        v_jobs = await visa_adapter.search(query="", filters={"pages": visa_pages})
        all_scanned_jobs.extend(v_jobs)
    except Exception as e:
        scan_logger.warning(f"Visa adapter scan error: {e}")

    # 2. Remotive Multi-Category
    remotive_adapter = RemotiveAdapter()
    try:
        r_jobs = await remotive_adapter.search(filters={"categories": ["devops-sysadmin", "software-dev", "data"]})
        all_scanned_jobs.extend(r_jobs)
    except Exception as e:
        scan_logger.warning(f"Remotive adapter scan error: {e}")

    # 3. Jobicy Multi-Tag
    jobicy_adapter = JobicyAdapter()
    try:
        j_jobs = await jobicy_adapter.search(filters={"tags": ["devops", "security", "sysadmin", "cloud", "python", "data"]})
        all_scanned_jobs.extend(j_jobs)
    except Exception as e:
        scan_logger.warning(f"Jobicy adapter scan error: {e}")

    # 4. Himalayas Rotating Offsets
    himalayas_adapter = HimalayasAdapter()
    try:
        h_jobs = await himalayas_adapter.search(filters={"offsets": him_offsets})
        all_scanned_jobs.extend(h_jobs)
    except Exception as e:
        scan_logger.warning(f"Himalayas adapter scan error: {e}")

    # 5. RemoteOK Global Tech
    remote_adapter = RemoteOKAdapter()
    try:
        rok_jobs = await remote_adapter.search(query="")
        all_scanned_jobs.extend(rok_jobs)
    except Exception as e:
        scan_logger.warning(f"RemoteOK adapter scan error: {e}")

    # 6. UN Jobs & Humanitarian Live Feeds (rotating queries)
    un_adapter = UNJobsAdapter()
    for q in un_queries:
        try:
            un_list = await un_adapter.search(query=q)
            all_scanned_jobs.extend(un_list)
        except Exception as e:
            scan_logger.warning(f"UNJobs scan error ({q}): {e}")

    # 7. ReliefWeb Category Search Feeds (rotating queries)
    relief_adapter = ReliefWebAdapter()
    for q in rw_queries:
        try:
            rw_list = await relief_adapter.search(query=q)
            all_scanned_jobs.extend(rw_list)
        except Exception as e:
            scan_logger.warning(f"ReliefWeb scan error ({q}): {e}")

    # 8. WeWorkRemotely Feeds
    wwr_adapter = WeWorkRemotelyAdapter()
    try:
        wwr_list = await wwr_adapter.search(query="devops")
        all_scanned_jobs.extend(wwr_list)
    except Exception as e:
        scan_logger.warning(f"WWR scan error: {e}")

    # 9. Global Fellowships
    fellowship_adapter = GlobalFellowshipAdapter()
    try:
        f_jobs = await fellowship_adapter.search(query="fellowship")
        all_scanned_jobs.extend(f_jobs)
    except Exception as e:
        scan_logger.warning(f"Fellowships scan error: {e}")

    scanned_count = len(all_scanned_jobs)

    # Ingest, Deduplicate, Store, and Score for ALL Candidate Pools
    for j in all_scanned_jobs:
        is_dup, _ = Deduplicator.is_duplicate(j, existing_jobs)
        if not is_dup:
            raw_hash = Deduplicator.compute_fingerprint(j["title"], j["employer"], j["description"])

            # Extra dedup: check if raw_hash already exists in DB
            hash_check = await db.execute(select(Job).where(Job.raw_hash == raw_hash).limit(1))
            if hash_check.scalar_one_or_none():
                continue

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
            try:
                await db.flush()
            except Exception:
                await db.rollback()
                continue

            visa_sig, _ = VisaDetector.evaluate(j["title"], j["description"], j["employer"])

            # Dynamically extract skills mentioned in the job text across registered candidate skill pools
            job_text = f"{j.get('title', '')} {j.get('description', '')}".lower()
            all_known_skills = {
                s.get("skill", "").strip().lower()
                for c_entry in candidate_profile_dicts
                for s in c_entry["dict"].get("skills", [])
                if s.get("skill")
            }
            job_skills = [sk for sk in all_known_skills if sk in job_text]

            features = JobFeature(
                job_id=job_obj.id,
                skills_json=job_skills,
                seniority=j.get("seniority") or "Mid-Senior",
                industry=j.get("industry") or "General",
                visa_signal=visa_sig or "indicated",
                remote_signal="full_remote" if j["work_mode"] == "remote" else "hybrid",
                extracted_salary={"min": j["salary_min"], "max": j["salary_max"], "currency": j["currency"]}
            )
            db.add(features)
            await db.flush()

            # Score this job for EVERY candidate pool in the system
            for c_entry in candidate_profile_dicts:
                c_prof = c_entry["profile"]
                c_dict = c_entry["dict"]
                match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
                    profile_data=c_dict,
                    job_data=j,
                    job_features={"skills_json": features.skills_json, "visa_signal": features.visa_signal}
                )

                db.add(JobMatch(
                    job_id=job_obj.id,
                    profile_id=c_prof.id,
                    match_score=match_score,
                    opportunity_score=opp_score,
                    explanation_json=explanation,
                    gaps_json=gaps
                ))

            existing_jobs.append(j)
            new_jobs_added += 1

    await db.commit()

    # ── Auto-Apply to all high-fit jobs discovered during scan ──
    stmt = (
        select(Job, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .where(JobMatch.match_score >= 80)
        .order_by(desc(JobMatch.created_at))
    )
    res = await db.execute(stmt)
    high_matches = res.all()

    auto_applied_count = 0
    for j_obj, match in high_matches:
        try:
            # Find the corresponding profile
            target_prof = next((p for p in all_profiles if p.id == match.profile_id), primary_profile)
            applied = await AutoApplier.process_job(
                db=db,
                job=j_obj,
                profile=target_prof,
                match_score=match.match_score,
                opportunity_score=match.opportunity_score,
                explanation=match.explanation_json or {}
            )
            if applied:
                auto_applied_count += 1
        except Exception as e:
            scan_logger.warning(f"Auto-apply error on job {j_obj.id}: {e}")

    return {
        "status": "success",
        "message": f"Global scan complete: scanned {scanned_count} jobs across live feeds.",
        "scanned_count": scanned_count,
        "new_jobs_added": new_jobs_added,
        "auto_applied_count": auto_applied_count,
        "cycle": cycle
    }
