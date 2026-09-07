import html
import logging
import re
import httpx
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """Utility to strip HTML tags for plain text fallback."""
    return re.sub(r"<[^>]+>", "", text)


class TelegramService:
    @staticmethod
    async def send_job_alert(
        bot_token: str,
        chat_id: str,
        job_data: Dict[str, Any],
        match_score: int,
        opportunity_score: int,
        reasons: list,
        application_id: Optional[str] = None,
        candidate_name: str = "Candidate",
        cv_filename: Optional[str] = None
    ) -> bool:
        """
        Dispatches a high-signal Telegram notification card with interactive inline action buttons.
        Uses robust HTML formatting with safe escaping and plain-text fallback.
        """
        if not bot_token or not chat_id:
            logger.warning("Telegram bot token or chat ID missing.")
            return False

        title = html.escape(str(job_data.get("title", "Position")))
        employer = html.escape(str(job_data.get("employer", "Company")))
        location = html.escape(str(job_data.get("location", "Global")))
        work_mode = html.escape(str(job_data.get("work_mode", "Remote")).title())
        raw_url = str(job_data.get("canonical_url", "http://localhost:3000")).strip()
        safe_url = raw_url if raw_url.startswith("http") else "https://reliefweb.int"
        c_name = html.escape(str(candidate_name))
        cv_text = html.escape(str(cv_filename)) if cv_filename else None

        escaped_reasons = [f"• {html.escape(str(r))}" for r in reasons[:3]]
        reasons_block = "\n".join(escaped_reasons) if escaped_reasons else "• High role relevance"

        # Rich HTML Card
        html_text = (
            f"⚡ <b>HIGH-SIGNAL MATCH DETECTED</b>\n\n"
            f"👤 <b>Candidate</b>: <code>{c_name}</code>\n"
            f"🎯 <b>Role</b>: <code>{title}</code>\n"
            f"🏢 <b>Employer</b>: {employer}\n"
            f"📍 <b>Location</b>: {location} ({work_mode})\n\n"
            f"📊 <b>Match Score</b>: <code>{match_score}%</code> | <b>Opportunity</b>: <code>{opportunity_score}%</code>\n\n"
            f"💡 <b>Key Match Reasons</b>:\n{reasons_block}\n\n"
            f"🌐 <b>Application Method</b>: Online Employer Portal / ATS\n"
            + (f"📎 <b>CV</b>: Prepared (<code>{cv_text}</code>)" if cv_text else "📎 <b>CV</b>: Prepared")
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "🌐 Apply on Company Portal (1-Click)",
                        "url": safe_url
                    }
                ]
            ]
        }

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
            "disable_web_page_preview": False
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(api_url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Telegram alert successfully sent to chat {chat_id}")
                    return True

                # Fallback to plain text if HTML entity parsing fails
                logger.warning(f"Telegram HTML send failed ({res.status_code}: {res.text}), attempting plain-text fallback...")
                plain_payload = {
                    "chat_id": chat_id,
                    "text": _strip_html(html_text),
                    "reply_markup": reply_markup,
                    "disable_web_page_preview": False
                }
                fallback_res = await client.post(api_url, json=plain_payload)
                if fallback_res.status_code == 200:
                    logger.info(f"Telegram alert delivered via plain-text fallback to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram plain-text fallback also failed ({fallback_res.status_code}): {fallback_res.text}")
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram message: {e}")

        return False

    @staticmethod
    async def send_auto_applied_notification(
        bot_token: str,
        chat_id: str,
        job_data: Dict[str, Any],
        match_score: int,
        opportunity_score: int,
        recipient_email: str,
        gmail_msg_id: Optional[str] = None,
        candidate_name: str = "Candidate",
        sender_email: str = "",
        cv_filename: Optional[str] = None
    ) -> bool:
        """
        Dispatches a clean Telegram receipt notification confirming an application was sent automatically.
        Uses robust HTML formatting with plain-text fallback.
        """
        if not bot_token or not chat_id:
            return False

        title = html.escape(str(job_data.get("title", "Position")))
        employer = html.escape(str(job_data.get("employer", "Company")))
        location = html.escape(str(job_data.get("location", "Worldwide")))
        work_mode = html.escape(str(job_data.get("work_mode", "Remote")).title())
        raw_url = str(job_data.get("canonical_url", "http://localhost:3000")).strip()
        safe_url = raw_url if raw_url.startswith("http") else "http://localhost:3000"
        c_name = html.escape(str(candidate_name))
        r_email = html.escape(str(recipient_email))
        s_email = html.escape(str(sender_email or "Authorized Candidate Account"))
        cv_text = html.escape(str(cv_filename)) if cv_filename else None
        msg_id_text = html.escape(str(gmail_msg_id)) if gmail_msg_id else None

        html_text = (
            f"🚀 <b>APPLICATION AUTO-SENT VIA GMAIL</b>\n\n"
            f"👤 <b>Candidate</b>: <code>{c_name}</code>\n"
            f"🎯 <b>Role</b>: <code>{title}</code>\n"
            f"🏢 <b>Employer</b>: {employer}\n"
            f"📍 <b>Location</b>: {location} ({work_mode})\n"
            f"📊 <b>Fit</b>: Match <code>{match_score}%</code> | Opp <code>{opportunity_score}%</code>\n\n"
            f"✉️ <b>Sent To</b>: <code>{r_email}</code>\n"
            f"📤 <b>From</b>: <code>{s_email}</code>\n"
            + (f"📎 <b>Attachment</b>: <code>{cv_text}</code>\n" if cv_text else "")
            + (f"🆔 <b>Gmail ID</b>: <code>{msg_id_text}</code>\n\n" if msg_id_text else "\n")
            + f"🔗 <a href=\"{safe_url}\">View Job Details</a>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "🌐 View Original Job Posting",
                        "url": safe_url
                    }
                ]
            ]
        }

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
            "disable_web_page_preview": False
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(api_url, json=payload)
                if res.status_code == 200:
                    return True

                # Plain-text retry
                logger.warning(f"Telegram HTML auto-apply notification failed ({res.status_code}), retrying plain text...")
                plain_payload = {
                    "chat_id": chat_id,
                    "text": _strip_html(html_text),
                    "reply_markup": reply_markup,
                    "disable_web_page_preview": False
                }
                fallback_res = await client.post(api_url, json=plain_payload)
                return fallback_res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to dispatch auto-applied Telegram notification: {e}")
            return False

    @staticmethod
    async def send_raw_message(
        bot_token: str,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "HTML"
    ) -> bool:
        """Send an arbitrary Telegram message with auto plain-text retry if formatting fails."""
        if not bot_token or not chat_id:
            return False

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(api_url, json=payload)
                if res.status_code == 200:
                    return True

                if parse_mode:
                    logger.warning(f"Telegram raw send error {res.status_code}: {res.text}, retrying as plain text...")
                    plain_payload = {
                        "chat_id": chat_id,
                        "text": _strip_html(text),
                        "disable_web_page_preview": True
                    }
                    fallback_res = await client.post(api_url, json=plain_payload)
                    return fallback_res.status_code == 200
                else:
                    logger.error(f"Telegram raw send error {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Telegram raw send exception: {e}")
        return False
