"""
AI Job Hunter — Application Pipeline & Package Generation Routes
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import session_factory
from app.models import (
    Application, Document, ApplicationAnswer, Job, JobMatch, JobFeature,
    CandidateProfile, CandidateSkill, Experience, Education, Certification, AuditLog, User
)
from app.schemas import (
    ApplicationResponse, ApplicationPrepareRequest, ApplicationActionRequest,
    DocumentResponse, ApplicationAnswerResponse
)
from app.services.application_generator import ApplicationGenerator
from app.services.gmail_service import GmailService
from app.api.routes.candidate import get_or_create_default_profile
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


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    status: Optional[str] = None,
    profile_id: Optional[str] = Query(None, description="Optional profile ID to filter applications"),
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
    
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
    profile_id: Optional[str] = Query(None),
    payload: Optional[ApplicationPrepareRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    profile = await get_or_create_default_profile(db, profile_id)
    
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

    # Load candidate user record
    user_res = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_res.scalar_one_or_none()

    # Build Candidate Dictionary
    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
    skills = skills_res.scalars().all()
    exp_res = await db.execute(select(Experience).where(Experience.profile_id == profile.id))
    experiences = exp_res.scalars().all()
    cert_res = await db.execute(select(Certification).where(Certification.profile_id == profile.id))
    certifications = cert_res.scalars().all()

    prof_dict = {
        "name": user.name if user else "Candidate",
        "email": user.email if user else "",
        "seniority": profile.seniority or "Specialist",
        "location": profile.location or "Nigeria",
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
    # ─── Load application & linked job ───
    stmt = select(Application).where(Application.id == id)
    res = await db.execute(stmt)
    app_obj = res.scalar_one_or_none()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    job_res = await db.execute(select(Job).where(Job.id == app_obj.job_id))
    job = job_res.scalar_one_or_none()

    # ─── Load cover letter document ───
    doc_res = await db.execute(
        select(Document).where(
            Document.application_id == app_obj.id,
            Document.type == "cover_letter"
        )
    )
    cover_letter_doc = doc_res.scalar_one_or_none()
    cover_letter_text = cover_letter_doc.content_markdown if cover_letter_doc else ""

    # ─── Resolve recruiter email from job description or features ───
    recruiter_email = None
    if job:
        # Try to extract email from the job description text
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        if job.description:
            found = re.findall(email_pattern, job.description)
            if found:
                recruiter_email = found[0]

        # Try job features (some scrapers store apply_email there)
        if not recruiter_email:
            feat_res = await db.execute(
                select(JobFeature).where(JobFeature.job_id == job.id)
            )
            for feat in feat_res.scalars().all():
                if feat.key in ("apply_email", "contact_email", "email"):
                    recruiter_email = feat.value
                    break

    # Fallback: send to yourself so you can forward it
    if not recruiter_email:
        recruiter_email = "davidolagbenro35@gmail.com"
        logger.warning(f"No recruiter email found for job {app_obj.job_id} — sending to self for review.")

    # ─── Build email body from cover letter ───
    job_title = job.title if job else "the position"
    employer = job.employer if job else "your organisation"
    cover_html = cover_letter_text.replace("\n", "<br>") if cover_letter_text else (
        f"Dear Hiring Manager,<br><br>"
        f"I am writing to express my strong interest in the <b>{job_title}</b> role at <b>{employer}</b>. "
        f"As a Senior IT and Communication Specialist with extensive experience in Cybersecurity and ICT4D, "
        f"I am confident I can make a significant contribution to your team.<br><br>"
        f"Please find my CV attached for your review.<br><br>"
        f"Best regards,<br><b>David Olagbenro</b><br>davidolagbenro35@gmail.com"
    )

    body_html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:680px;margin:0 auto;line-height:1.6">
      <p>{cover_html}</p>
      <hr style="border:1px solid #eee;margin:24px 0">
      <p style="font-size:12px;color:#999">This application was submitted via AI Job Hunter on behalf of David Olagbenro.</p>
    </body></html>
    """

    # ─── Send via Gmail with CV attached ───
    user_res = await db.execute(select(User).limit(1))
    user = user_res.scalar_one_or_none()
    gmail_result = {"status": "skipped", "reason": "no_gmail_tokens"}

    if user and user.google_tokens_encrypted:
        try:
            tokens = json.loads(user.google_tokens_encrypted)
            access_token = tokens.get("access_token")
            sender_email = tokens.get("gmail_address", user.email)

            # Try to find the CV file
            cv_path = Path(settings.cv_pdf_path)
            if not cv_path.exists():
                cv_path = Path("apps/api") / settings.cv_pdf_path

            gmail_result = await GmailService.send_application_email(
                access_token=access_token,
                sender_email=sender_email,
                to_email=recruiter_email,
                subject=f"Application: {job_title} — David Olagbenro | Senior ICT Specialist",
                body_html=body_html,
                cv_path=str(cv_path) if cv_path.exists() else None,
                cv_filename=settings.cv_filename
            )

            # If token expired, attempt refresh
            if gmail_result.get("status_code") == 401:
                refresh_token = tokens.get("refresh_token")
                if refresh_token:
                    new_token = await GmailService.refresh_access_token(refresh_token)
                    if new_token:
                        tokens["access_token"] = new_token
                        user.google_tokens_encrypted = json.dumps(tokens)
                        db.add(user)
                        gmail_result = await GmailService.send_application_email(
                            access_token=new_token,
                            sender_email=sender_email,
                            to_email=recruiter_email,
                            subject=f"Application: {job_title} — David Olagbenro | Senior ICT Specialist",
                            body_html=body_html,
                            cv_path=str(cv_path) if cv_path.exists() else None,
                            cv_filename=settings.cv_filename
                        )
        except Exception as e:
            logger.error(f"Gmail send error during approve: {e}")
            gmail_result = {"status": "error", "error": str(e)}

    # ─── Update application record ───
    app_obj.status = "APPLIED"
    app_obj.applied_at = datetime.now(timezone.utc)
    app_obj.approval_state = "AUTO"

    db.add(AuditLog(
        action="APPROVE_AND_APPLY",
        entity_type="application",
        entity_id=app_obj.id,
        metadata_json={
            "applied_at": str(app_obj.applied_at),
            "recruiter_email": recruiter_email,
            "gmail_status": gmail_result.get("status"),
            "gmail_message_id": gmail_result.get("message_id"),
            "note": action.reason if action else None
        }
    ))

    await db.commit()
    logger.info(f"Application {id} APPROVED — email {gmail_result.get('status')} to {recruiter_email}")

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


@router.post("/auto-apply")
async def trigger_auto_apply_all(
    min_score: int = 80,
    db: AsyncSession = Depends(get_db)
):
    """
    Scans all high-match jobs in the database and automatically:
    1. Generates tailored cover letter
    2. Sends email via Gmail with David's CV attached
    3. Marks application as APPLIED in Kanban
    4. Sends instant Telegram confirmation receipt
    """
    from app.services.auto_applier import AutoApplier
    profile = await get_or_create_default_profile(db)

    # Find all matches >= min_score
    stmt = (
        select(Job, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .where(JobMatch.match_score >= min_score)
        .order_by(desc(JobMatch.match_score))
    )
    res = await db.execute(stmt)
    pairs = res.all()

    applied_results = []
    for job, match in pairs:
        result = await AutoApplier.process_job(
            db=db,
            job=job,
            profile=profile,
            match_score=match.match_score,
            opportunity_score=match.opportunity_score,
            explanation=match.explanation_json or {}
        )
        if result:
            applied_results.append(result)

    return {
        "status": "success",
        "processed_count": len(pairs),
        "auto_applied_count": len(applied_results),
        "applications": applied_results
    }

