"""
AI Job Hunter — Auto-Apply Engine
Automatically generates tailored packages, dispatches application emails with CV attached,
and sends instant Telegram receipts without waiting for manual approval.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Job, Application, Document, ApplicationAnswer, AuditLog, User, CandidateProfile, CandidateSkill, Experience, Certification
from app.services.application_generator import ApplicationGenerator
from app.services.gmail_service import GmailService
from app.services.telegram_service import TelegramService
from app.config import settings

logger = logging.getLogger(__name__)

# Minimum match threshold for auto-applying
AUTO_APPLY_MATCH_THRESHOLD = 80


class AutoApplier:
    @staticmethod
    async def process_job(
        db: AsyncSession,
        job: Job,
        profile: CandidateProfile,
        match_score: int,
        opportunity_score: int,
        explanation: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a matched job. If match_score >= AUTO_APPLY_MATCH_THRESHOLD:
        1. Generates tailored cover letter & documents
        2. Dispatches email via Gmail API with CV attached
        3. Records Application in DB with status APPLIED
        4. Sends instant Telegram confirmation receipt to David
        """
        if match_score < AUTO_APPLY_MATCH_THRESHOLD:
            return None

        # Check if already applied to this job
        stmt = select(Application).where(
            Application.job_id == job.id,
            Application.profile_id == profile.id
        )
        res = await db.execute(stmt)
        existing_app = res.scalar_one_or_none()
        if existing_app:
            return None  # Already processed

        # ── 1. Load Candidate Context for Application Generator ──
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
            "experiences": [
                {"employer": e.employer, "title": e.title, "start_date": e.start_date, "end_date": e.end_date, "description": e.description, "sector": e.sector}
                for e in experiences
            ],
            "certifications": [{"name": c.name, "issuer": c.issuer, "year": c.year} for c in certifications]
        }

        job_dict = {
            "title": job.title,
            "employer": job.employer,
            "location": job.location,
            "description": job.description
        }

        # Generate Tailored Package
        pkg = ApplicationGenerator.generate_package(prof_dict, job_dict, explanation)

        # ── 2. Create Application Record in DB ──
        app_obj = Application(
            job_id=job.id,
            profile_id=profile.id,
            status="APPLIED",
            approval_state="AUTO",
            method="email",
            applied_at=datetime.now(timezone.utc)
        )
        db.add(app_obj)
        await db.flush()

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

        # ── 3. Extract Recruiter Email or Destination ──
        recruiter_email = None
        if job.description:
            email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
            found = re.findall(email_pattern, job.description)
            if found:
                recruiter_email = found[0]

        if not recruiter_email:
            # Smart fallback: send to David's verified Gmail so he has a copy ready to 1-click forward
            recruiter_email = "davidolagbenro35@gmail.com"

        # ── 4. Format HTML Body & Send via Gmail ──
        cover_html = pkg["cover_letter"].replace("\n", "<br>")
        body_html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:680px;margin:0 auto;line-height:1.6">
          <p>{cover_html}</p>
          <hr style="border:1px solid #eee;margin:24px 0">
          <p style="font-size:12px;color:#888">Submitted by AI Job Hunter on behalf of David Olagbenro.</p>
        </body></html>
        """

        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        gmail_result = {"status": "skipped"}

        if user and user.google_tokens_encrypted:
            try:
                tokens = json.loads(user.google_tokens_encrypted)
                access_token = tokens.get("access_token")
                sender_email = tokens.get("gmail_address", "davidolagbenro35@gmail.com")

                cv_path = Path(settings.cv_pdf_path)
                if not cv_path.exists():
                    cv_path = Path("apps/api") / settings.cv_pdf_path

                gmail_result = await GmailService.send_application_email(
                    access_token=access_token,
                    sender_email=sender_email,
                    to_email=recruiter_email,
                    subject=f"Application: {job.title} — David Olagbenro | Senior ICT Specialist",
                    body_html=body_html,
                    cv_path=str(cv_path) if cv_path.exists() else None,
                    cv_filename=settings.cv_filename
                )

                # If token expired, refresh and retry
                if gmail_result.get("status_code") == 401 and tokens.get("refresh_token"):
                    new_token = await GmailService.refresh_access_token(tokens["refresh_token"])
                    if new_token:
                        tokens["access_token"] = new_token
                        user.google_tokens_encrypted = json.dumps(tokens)
                        db.add(user)
                        gmail_result = await GmailService.send_application_email(
                            access_token=new_token,
                            sender_email=sender_email,
                            to_email=recruiter_email,
                            subject=f"Application: {job.title} — David Olagbenro | Senior ICT Specialist",
                            body_html=body_html,
                            cv_path=str(cv_path) if cv_path.exists() else None,
                            cv_filename=settings.cv_filename
                        )
            except Exception as e:
                logger.error(f"Auto-apply Gmail dispatch error: {e}")
                gmail_result = {"status": "error", "error": str(e)}

        # ── 5. Audit Log ──
        db.add(AuditLog(
            action="AUTO_APPLY_DISPATCHED",
            entity_type="application",
            entity_id=app_obj.id,
            metadata_json={
                "job_id": job.id,
                "title": job.title,
                "employer": job.employer,
                "recruiter_email": recruiter_email,
                "gmail_status": gmail_result.get("status"),
                "message_id": gmail_result.get("message_id")
            }
        ))
        await db.commit()

        # ── 6. Send Immediate Telegram Receipt Notification ──
        if settings.telegram_bot_token and settings.telegram_chat_id:
            await TelegramService.send_auto_applied_notification(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                job_data={
                    "title": job.title,
                    "employer": job.employer,
                    "location": job.location,
                    "work_mode": job.work_mode,
                    "canonical_url": job.canonical_url
                },
                match_score=match_score,
                opportunity_score=opportunity_score,
                recipient_email=recruiter_email,
                gmail_msg_id=gmail_result.get("message_id")
            )

        logger.info(f"✅ AUTO-APPLIED: {job.title} at {job.employer} -> {recruiter_email}")
        return {
            "application_id": app_obj.id,
            "job_title": job.title,
            "employer": job.employer,
            "email_status": gmail_result.get("status"),
            "recipient": recruiter_email
        }
