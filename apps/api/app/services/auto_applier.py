"""
AI Job Hunter — Auto-Apply Engine
Automatically evaluates matched global jobs.
Strict Rule: ONLY dispatches Gmail if a verified company/HR email is found.
Never sends emails to David's own address. For web portal jobs, notifies Telegram with direct apply links.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Job, Application, Document, AuditLog, User, CandidateProfile, CandidateSkill, Experience, Certification
from app.services.application_generator import ApplicationGenerator
from app.services.gmail_service import GmailService
from app.services.telegram_service import TelegramService
from app.services.hr_email_resolver import HREmailResolver
from app.config import settings

logger = logging.getLogger(__name__)

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
        - Resolves genuine HR email
        - If HR email found: Sends tailored email + CV directly to employer HR and notifies Telegram
        - If portal-only: Saves application and sends Telegram card with direct apply link (no email sent)
        """
        if match_score < AUTO_APPLY_MATCH_THRESHOLD:
            return None

        # Check if already processed
        stmt = select(Application).where(
            Application.job_id == job.id,
            Application.profile_id == profile.id
        )
        res = await db.execute(stmt)
        existing_app = res.scalar_one_or_none()
        if existing_app:
            return None

        # ── 1. Load Candidate Context ──
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

        # Generate Clean Tailored Package
        pkg = ApplicationGenerator.generate_package(prof_dict, job_dict, explanation)

        # ── 2. Resolve Genuine Employer HR Email (with live deep page scraping) ──
        recruiter_email, method = await HREmailResolver.async_resolve_recipient(
            description=job.description or "",
            canonical_url=job.canonical_url or "",
            employer=job.employer or ""
        )


        # ── 3. Create Application Record in DB ──
        app_obj = Application(
            job_id=job.id,
            profile_id=profile.id,
            status="APPLIED" if recruiter_email else "PORTAL_READY",
            approval_state="AUTO",
            method=method,
            applied_at=datetime.now(timezone.utc) if recruiter_email else None
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

        # ── 4. Send Email ONLY if genuine HR recipient exists ──
        gmail_result = {"status": "skipped", "reason": "portal_only"}

        if recruiter_email and "davidolagbenro" not in recruiter_email:
            clean_cover_html = "".join([f"<p style='margin:0 0 14px 0;line-height:1.6;'>{p.strip()}</p>" for p in pkg["cover_letter"].split("\n\n") if p.strip()])
            body_html = f"""
            <html>
            <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#222;font-size:15px;max-width:650px;margin:0 auto;padding:20px;">
              {clean_cover_html}
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0 12px 0;">
              <p style="font-size:12px;color:#94a3b8;margin:0;">Submitted on behalf of David Olagbenro — Senior IT & Communication Specialist.</p>
            </body>
            </html>
            """

            user_res = await db.execute(select(User).limit(1))
            user = user_res.scalar_one_or_none()

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
                        subject=f"Application: {job.title} — David Olagbenro",
                        body_html=body_html,
                        cv_path=str(cv_path) if cv_path.exists() else None,
                        cv_filename=settings.cv_filename
                    )

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
                                subject=f"Application: {job.title} — David Olagbenro",
                                body_html=body_html,
                                cv_path=str(cv_path) if cv_path.exists() else None,
                                cv_filename=settings.cv_filename
                            )
                except Exception as e:
                    logger.error(f"Gmail send error: {e}")
                    gmail_result = {"status": "error", "error": str(e)}

        # ── 5. Audit Log ──
        db.add(AuditLog(
            action="AUTO_APPLY_DISPATCHED" if recruiter_email else "PORTAL_APPLICATION_PREPARED",
            entity_type="application",
            entity_id=app_obj.id,
            metadata_json={
                "job_id": job.id,
                "title": job.title,
                "employer": job.employer,
                "recruiter_email": recruiter_email,
                "method": method,
                "gmail_status": gmail_result.get("status"),
                "message_id": gmail_result.get("message_id")
            }
        ))
        await db.commit()

        # ── 6. Send Telegram Notification ──
        if settings.telegram_bot_token and settings.telegram_chat_id:
            if recruiter_email:
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
            else:
                # For web portal roles, notify with clean link and ready status
                await TelegramService.send_job_alert(
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
                    reasons=explanation.get("match_reasons", ["High-value role compatibility"]),
                    application_id=app_obj.id
                )

        logger.info(f"Auto-apply processed for {job.title} at {job.employer} (Method: {method})")
        return {
            "application_id": app_obj.id,
            "job_title": job.title,
            "employer": job.employer,
            "email_status": gmail_result.get("status"),
            "recipient": recruiter_email,
            "method": method
        }
