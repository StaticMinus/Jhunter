"""
AI Job Hunter — Telegram Bot Alert & Quick-Action Dispatcher Service
"""

import logging
import httpx
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    @staticmethod
    async def send_job_alert(
        bot_token: str,
        chat_id: str,
        job_data: Dict[str, Any],
        match_score: int,
        opportunity_score: int,
        reasons: list,
        application_id: Optional[str] = None
    ) -> bool:
        """
        Dispatches a high-signal Telegram notification card with interactive inline action buttons.
        """
        if not bot_token or not chat_id:
            logger.warning("Telegram bot token or chat ID missing.")
            return False

        title = job_data.get("title", "Position")
        employer = job_data.get("employer", "Company")
        location = job_data.get("location", "Global")
        work_mode = job_data.get("work_mode", "Remote").title()
        url = job_data.get("canonical_url", "http://localhost:3000")

        # Format Rich Markdown Card
        text = (
            f"⚡ *HIGH-SIGNAL JOB MATCH DETECTED*\n\n"
            f"🎯 *Role*: `{title}`\n"
            f"🏢 *Employer*: {employer}\n"
            f"📍 *Location*: {location} ({work_mode})\n\n"
            f"📊 *Match Score*: `{match_score}%` | *Opportunity*: `{opportunity_score}%` \n\n"
            f"💡 *Key Match Reasons*:\n"
            + "\n".join([f"• {r}" for r in reasons[:3]])
            + f"\n\n🔗 [View Job Posting]({url})"
        )

        # Inline Action Keyboard Buttons
        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Approve & Apply via Gmail",
                        "callback_data": f"approve_{application_id or 'demo'}"
                    }
                ],
                [
                    {
                        "text": "📝 Review Package in Studio",
                        "callback_data": f"review_{application_id or 'demo'}"
                    },
                    {
                        "text": "❌ Skip / Archive",
                        "callback_data": f"reject_{application_id or 'demo'}"
                    }
                ]
            ]
        }

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup,
            "disable_web_page_preview": False
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(api_url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Telegram alert successfully sent to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram API error {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram message: {e}")

        return False
