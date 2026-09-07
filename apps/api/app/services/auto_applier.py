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


def _has_valid_gmail_tokens(user: Optional[User]) -> bool:
    """Check if a user has REAL OAuth tokens or if GMAIL_REFRESH_TOKEN is set in settings."""
    if not user:
        return bool(getattr(settings, "gmail_refresh_token", None))
    if user.google_tokens_encrypted:
        try:
            tokens = json.loads(user.google_tokens_encrypted)
            if "web" in tokens and "access_token" not in tokens and "refresh_token" not in tokens:
                return False
            if bool(tokens.get("access_token")) or bool(tokens.get("refresh_token")):
                return True
        except (json.JSONDecodeError, Exception):
            pass
    # Fall back to settings.gmail_refresh_token only for David (the default candidate)
    if user.email == settings.default_candidate_email:
        return bool(getattr(settings, "gmail_refresh_token", None))
    return False


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
        user_res = await db.execute(select(User).where(User.id == profile.user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            user_res = await db.execute(select(User).limit(1))
            user = user_res.scalar_one_or_none()

        candidate_name = user.name if user else "Candidate"
        candidate_email = user.email if user else settings.default_candidate_email
        candidate_title = profile.seniority or "Professional"
        # Per-profile CV: use profile's own CV if set, otherwise fall back to global settings
        cv_filename = profile.cv_filename or settings.cv_filename
        cv_profile_path = profile.cv_storage_path  # may be None

        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.profile_id == profile.id))
        skills = skills_res.scalars().all()
        exp_res = await db.execute(select(Experience).where(Experience.profile_id == profile.id))
        experiences = exp_res.scalars().all()
        cert_res = await db.execute(select(Certification).where(Certification.profile_id == profile.id))
        certifications = cert_res.scalars().all()

        prof_dict = {
            "name": candidate_name,
            "email": candidate_email,
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
            status="PORTAL_READY",
            approval_state="AUTO",
            method=method,
            applied_at=None
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
        sender_email = candidate_email  # default for Telegram notification

        # Prevent sending to the applicant's own email address
        is_self_email = recruiter_email and (candidate_email.lower() in recruiter_email.lower() or "davidolagbenro" in recruiter_email.lower())

        # ── DUPLICATE GUARD: Check if another candidate already emailed this job's recruiter ──
        already_emailed_this_job = False
        if recruiter_email and not is_self_email:
            dup_check = await db.execute(
                select(Application).where(
                    Application.job_id == job.id,
                    Application.status == "APPLIED",
                    Application.profile_id != profile.id
                )
            )
            if dup_check.scalar_one_or_none():
                already_emailed_this_job = True
                logger.info(
                    f"⏭️ Skipping email for {candidate_name} → {recruiter_email} "
                    f"(another candidate already applied to this job via email)"
                )

        # ── TOKEN GUARD: Only send if this user has REAL OAuth tokens ──
        has_tokens = _has_valid_gmail_tokens(user)
        if not has_tokens and recruiter_email and not is_self_email:
            logger.info(
                f"⏭️ Skipping email for {candidate_name} — no valid Gmail OAuth tokens. "
                f"Marking as PORTAL_READY."
            )

        if recruiter_email and not is_self_email and has_tokens and not already_emailed_this_job:
            clean_cover_html = "".join([f"<p style='margin:0 0 14px 0;line-height:1.6;'>{p.strip()}</p>" for p in pkg["cover_letter"].split("\n\n") if p.strip()])
            body_html = f"""
            <html>
            <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#222;font-size:15px;max-width:650px;margin:0 auto;padding:20px;">
              {clean_cover_html}
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0 12px 0;">
              <p style="font-size:12px;color:#94a3b8;margin:0;">Submitted on behalf of {candidate_name} — {candidate_title}.</p>
            </body>
            </html>
            """

            # Select CV attachment path — per-profile CV first, then global fallback
            cv_filename = profile.cv_filename or settings.cv_filename
            cv_candidates = []
            if cv_profile_path:
                cv_candidates.extend([
                    Path(cv_profile_path),
                    Path("apps/api") / cv_profile_path,
                    Path("apps/api/cv_uploads") / Path(cv_profile_path).name,
                    Path("cv_uploads") / Path(cv_profile_path).name,
                ])
            cv_candidates.extend([
                Path(settings.cv_pdf_path),
                Path("apps/api") / settings.cv_pdf_path,
                Path(r"c:\Users\David\Music\JOB Hunter\apps\api\cv_david_ict_specialist.pdf"),
                Path(r"c:\Users\David\Music\JOB Hunter\cv_david_ict_specialist.pdf")
            ])

            cv_path = None
            for p in cv_candidates:
                if p.exists():
                    cv_path = str(p)
                    break

            try:
                tokens = {}
                if user and user.google_tokens_encrypted:
                    try:
                        tokens = json.loads(user.google_tokens_encrypted)
                    except Exception:
                        tokens = {}

                refresh_token = tokens.get("refresh_token")
                if not refresh_token and user and user.email == settings.default_candidate_email:
                    refresh_token = getattr(settings, "gmail_refresh_token", "")
                access_token = tokens.get("access_token")
                sender_email = tokens.get("gmail_address") or candidate_email

                client_id = tokens.get("client_id") or settings.google_client_id
                client_secret = tokens.get("client_secret") or settings.google_client_secret

                # Proactively obtain fresh access token to avoid 401s
                if refresh_token:
                    fresh_access = await GmailService.refresh_access_token(
                        refresh_token, client_id=client_id, client_secret=client_secret
                    )
                    if fresh_access:
                        access_token = fresh_access
                        tokens["access_token"] = fresh_access
                        tokens["refresh_token"] = refresh_token
                        tokens["gmail_address"] = sender_email
                        if user:
                            user.google_tokens_encrypted = json.dumps(tokens)
                            db.add(user)

                gmail_result = await GmailService.send_application_email(
                    access_token=access_token,
                    sender_email=sender_email,
                    to_email=recruiter_email,
                    subject=f"Application: {job.title} — {candidate_name}",
                    body_html=body_html,
                    cv_path=cv_path,
                    cv_filename=cv_filename
                )

                if gmail_result.get("status_code") == 401 and refresh_token:
                    new_token = await GmailService.refresh_access_token(
                        refresh_token,
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    if new_token:
                        tokens["access_token"] = new_token
                        if user:
                            user.google_tokens_encrypted = json.dumps(tokens)
                            db.add(user)
                        gmail_result = await GmailService.send_application_email(
                            access_token=new_token,
                            sender_email=sender_email,
                            to_email=recruiter_email,
                            subject=f"Application: {job.title} — {candidate_name}",
                            body_html=body_html,
                            cv_path=cv_path,
                            cv_filename=cv_filename
                        )

                # Set application status based on real delivery result
                if gmail_result.get("status") == "sent":
                    app_obj.status = "APPLIED"
                    app_obj.applied_at = datetime.now(timezone.utc)
                    app_obj.external_reference = gmail_result.get("message_id")
                    logger.info(f"✅ Gmail successfully sent for {job.title} → {recruiter_email} (Msg ID: {gmail_result.get('message_id')})")
                else:
                    app_obj.status = "FAILED"
                    app_obj.external_reference = f"Send failed: {gmail_result.get('error', 'unknown error')[:200]}"
                    logger.error(f"❌ Gmail sending failed for {job.title} → {recruiter_email}: {gmail_result}")

            except Exception as e:
                logger.error(f"Gmail send exception for {candidate_name}: {e}")
                gmail_result = {"status": "error", "error": str(e)}
                app_obj.status = "FAILED"
                app_obj.external_reference = f"Exception: {str(e)[:200]}"

        elif recruiter_email and not is_self_email and (not has_tokens or already_emailed_this_job):
            # Keep as PORTAL_READY since email could not/should not be sent
            app_obj.status = "PORTAL_READY"
            app_obj.applied_at = None

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
        # Use per-user telegram_chat_id if available, otherwise fall back to global settings
        tg_chat_id = (user.telegram_chat_id if user and user.telegram_chat_id else settings.telegram_chat_id)
        if settings.telegram_bot_token and tg_chat_id:
            if recruiter_email and gmail_result.get("status") == "sent":
                await TelegramService.send_auto_applied_notification(
                    bot_token=settings.telegram_bot_token,
                    chat_id=tg_chat_id,
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
                    gmail_msg_id=gmail_result.get("message_id"),
                    candidate_name=candidate_name,
                    sender_email=sender_email if (user and user.google_tokens_encrypted) else candidate_email,
                    cv_filename=cv_filename
                )
            else:
                # For web portal roles or un-sent applications, notify with clean link and ready status
                await TelegramService.send_job_alert(
                    bot_token=settings.telegram_bot_token,
                    chat_id=tg_chat_id,
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
                    application_id=app_obj.id,
                    candidate_name=candidate_name,
                    cv_filename=cv_filename
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
