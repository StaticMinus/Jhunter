"""
AI Job Hunter — Application Pipeline & Package Generation Routes
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import session_factory
from app.models import (
    Application, Document, ApplicationAnswer, Job, JobMatch, JobFeature,
    CandidateProfile, CandidateSkill, Experience, Education, Certification, AuditLog
)
from app.schemas import (
    ApplicationResponse, ApplicationPrepareRequest, ApplicationActionRequest,
    DocumentResponse, ApplicationAnswerResponse
)
from app.services.application_generator import ApplicationGenerator
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


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    
    stmt = select(Application).where(Application.profile_id == profile.id).order_by(desc(Application.created_at))
    if status:
        stmt = stmt.where(Application.status == status.upper())
    
    result = await db.execute(stmt)
    apps = result.scalars().all()

    output = []
    for a in apps:
        # Load documents & answers
        doc_res = await db.execute(select(Document).where(Document.application_id == a.id))
        docs = doc_res.scalars().all()

        ans_res = await db.execute(select(ApplicationAnswer).where(ApplicationAnswer.application_id == a.id))
        answers = ans_res.scalars().all()

        output.append(ApplicationResponse(
            id=a.id,
            job_id=a.job_id,
            profile_id=a.profile_id,
            status=a.status,
            approval_state=a.approval_state,
            applied_at=a.applied_at,
            method=a.method,
            created_at=a.created_at,
            documents=[DocumentResponse.model_validate(d) for d in docs],
            answers=[ApplicationAnswerResponse.model_validate(ans) for ans in answers]
        ))

    return output


@router.post("/{job_id}/prepare", response_model=ApplicationResponse)
async def prepare_application_package(
    job_id: str,
    payload: Optional[ApplicationPrepareRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db)
    
    job_res = await db.execute(select(Job).where(Job.id == job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == job.id, JobMatch.profile_id == profile.id))
    match = match_res.scalar_one_or_none()
    explanation = match.explanation_json if match else {}

    # Check if application already exists
    app_res = await db.execute(select(Application).where(Application.job_id == job.id, Application.profile_id == profile.id))
    app_obj = app_res.scalar_one_or_none()

    if not app_obj:
        app_obj = Application(
            job_id=job.id,
            profile_id=profile.id,
            status="PENDING_APPROVAL",
            approval_state="REVIEW" if (match and match.match_score < 90) else "AUTO",
            method="email"
        )
        db.add(app_obj)
        await db.flush()

    # Build Candidate Dictionary
    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    skills = skills_res.scalars().all()
    exp_res = await db.execute(select(Experience).where(Experience.profile_id == profile.id))
    experiences = exp_res.scalars().all()
    cert_res = await db.execute(select(Certification).where(Certification.profile_id == profile.id))
    certifications = cert_res.scalars().all()

    prof_dict = {
        "name": "David",
        "summary": profile.summary,
        "skills": [{"skill": s.skill} for s in skills],
        "experiences": [{"employer": e.employer, "title": e.title, "start_date": e.start_date, "end_date": e.end_date, "description": e.description, "sector": e.sector} for e in experiences],
        "certifications": [{"name": c.name, "issuer": c.issuer, "year": c.year} for c in certifications]
    }

    job_dict = {
        "title": job.title,
        "employer": job.employer,
        "location": job.location,
        "description": job.description
    }

    # Generate Anti-Fabrication Package
    pkg = ApplicationGenerator.generate_package(prof_dict, job_dict, explanation)

    # Save Cover Letter Document
    db.add(Document(
        application_id=app_obj.id,
        type="cover_letter",
        content_markdown=pkg["cover_letter"],
        storage_path=f"applications/{app_obj.id}/cover_letter.md"
    ))

    # Save Tailored CV Document
    db.add(Document(
        application_id=app_obj.id,
        type="tailored_cv",
        content_markdown=pkg["tailored_cv"],
        storage_path=f"applications/{app_obj.id}/tailored_cv.md"
    ))

    # Save Briefing
    db.add(Document(
        application_id=app_obj.id,
        type="briefing",
        content_markdown=pkg["briefing"],
        storage_path=f"applications/{app_obj.id}/briefing.md"
    ))

    # Save Application Answers
    for ans in pkg["answers"]:
        db.add(ApplicationAnswer(
            application_id=app_obj.id,
            question=ans["question"],
            answer=ans["answer"],
            confidence=ans["confidence"],
            flagged_for_review=ans["flagged_for_review"]
        ))

    # Log Audit Event
    db.add(AuditLog(
        action="PREPARE_APPLICATION",
        entity_type="application",
        entity_id=app_obj.id,
        metadata_json={"job_id": job.id, "employer": job.employer, "title": job.title}
    ))

    await db.commit()

    # Return refreshed object
    doc_res = await db.execute(select(Document).where(Document.application_id == app_obj.id))
    docs = doc_res.scalars().all()
    ans_res = await db.execute(select(ApplicationAnswer).where(ApplicationAnswer.application_id == app_obj.id))
    answers = ans_res.scalars().all()

    return ApplicationResponse(
        id=app_obj.id,
        job_id=app_obj.job_id,
        profile_id=app_obj.profile_id,
        status=app_obj.status,
        approval_state=app_obj.approval_state,
        applied_at=app_obj.applied_at,
        method=app_obj.method,
        created_at=app_obj.created_at,
        documents=[DocumentResponse.model_validate(d) for d in docs],
        answers=[ApplicationAnswerResponse.model_validate(ans) for ans in answers]
    )


@router.post("/{id}/approve", response_model=ApplicationResponse)
async def approve_application(
    id: str,
    action: Optional[ApplicationActionRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Application).where(Application.id == id)
    res = await db.execute(stmt)
    app_obj = res.scalar_one_or_none()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj.status = "APPLIED"
    app_obj.applied_at = datetime.now(timezone.utc)
    app_obj.approval_state = "AUTO"

    db.add(AuditLog(
        action="APPROVE_AND_APPLY",
        entity_type="application",
        entity_id=app_obj.id,
        metadata_json={"applied_at": str(app_obj.applied_at), "note": action.reason if action else None}
    ))

    await db.commit()

    doc_res = await db.execute(select(Document).where(Document.application_id == app_obj.id))
    docs = doc_res.scalars().all()
    ans_res = await db.execute(select(ApplicationAnswer).where(ApplicationAnswer.application_id == app_obj.id))
    answers = ans_res.scalars().all()

    return ApplicationResponse(
        id=app_obj.id,
        job_id=app_obj.job_id,
        profile_id=app_obj.profile_id,
        status=app_obj.status,
        approval_state=app_obj.approval_state,
        applied_at=app_obj.applied_at,
        method=app_obj.method,
        created_at=app_obj.created_at,
        documents=[DocumentResponse.model_validate(d) for d in docs],
        answers=[ApplicationAnswerResponse.model_validate(ans) for ans in answers]
    )


@router.post("/{id}/reject", response_model=ApplicationResponse)
async def reject_application(
    id: str,
    action: Optional[ApplicationActionRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Application).where(Application.id == id)
    res = await db.execute(stmt)
    app_obj = res.scalar_one_or_none()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj.status = "ARCHIVED"
    app_obj.approval_state = "SKIP"

    db.add(AuditLog(
        action="REJECT_APPLICATION",
        entity_type="application",
        entity_id=app_obj.id,
        metadata_json={"reason": action.reason if action else "Skipped by user"}
    ))

    await db.commit()

    doc_res = await db.execute(select(Document).where(Document.application_id == app_obj.id))
    docs = doc_res.scalars().all()
    ans_res = await db.execute(select(ApplicationAnswer).where(ApplicationAnswer.application_id == app_obj.id))
    answers = ans_res.scalars().all()

    return ApplicationResponse(
        id=app_obj.id,
        job_id=app_obj.job_id,
        profile_id=app_obj.profile_id,
        status=app_obj.status,
        approval_state=app_obj.approval_state,
        applied_at=app_obj.applied_at,
        method=app_obj.method,
        created_at=app_obj.created_at,
        documents=[DocumentResponse.model_validate(d) for d in docs],
        answers=[ApplicationAnswerResponse.model_validate(ans) for ans in answers]
    )
