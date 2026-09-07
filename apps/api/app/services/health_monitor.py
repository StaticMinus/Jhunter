"""
AI Job Hunter — Health Monitor & Heartbeat System
Sends periodic Telegram status reports and alerts on startup/shutdown/errors.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.telegram_service import TelegramService
from app.config import settings

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Tracks daemon health and sends periodic status reports to Telegram."""

    _startup_time: Optional[datetime] = None
    _total_scans: int = 0
    _total_new_jobs: int = 0
    _total_applied: int = 0
    _consecutive_errors: int = 0
    _last_error: Optional[str] = None

    @classmethod
    def record_startup(cls):
        cls._startup_time = datetime.now(timezone.utc)
        cls._total_scans = 0
        cls._total_new_jobs = 0
        cls._total_applied = 0
        cls._consecutive_errors = 0

    @classmethod
    def record_scan(cls, scanned: int, new_jobs: int, applied: int):
        cls._total_scans += 1
        cls._total_new_jobs += new_jobs
        cls._total_applied += applied
        cls._consecutive_errors = 0  # Reset on success

    @classmethod
    def record_error(cls, error: str):
        cls._consecutive_errors += 1
        cls._last_error = error

    @classmethod
    def get_uptime_str(cls) -> str:
        if not cls._startup_time:
            return "Unknown"
        delta = datetime.now(timezone.utc) - cls._startup_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m {seconds}s"

    @classmethod
    async def send_startup_alert(cls):
        """Notify Telegram that the daemon has started."""
        cls.record_startup()
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return

        import html
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        text = (
            f"🚀 <b>AI JOB HUNTER — DAEMON STARTED</b>\n\n"
            f"⏰ <b>Started</b>: <code>{now_str}</code>\n"
            f"🔄 <b>Scan Interval</b>: Every <code>{settings.scan_interval_seconds}</code> seconds\n"
            f"💓 <b>Heartbeat</b>: Every <code>{settings.heartbeat_interval_hours}</code> hours\n"
            f"🎯 <b>Status</b>: Online & scanning worldwide job feeds\n\n"
            f"📋 <b>Feeds</b>: ReliefWeb, RemoteOK, UN Jobs, Devex, Visa Boards, "
            f"Remotive, Jobicy, Himalayas, WeWorkRemotely, Fellowships"
        )
        await TelegramService.send_raw_message(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode="HTML"
        )

    @classmethod
    async def send_shutdown_alert(cls, reason: str = "Graceful shutdown"):
        """Notify Telegram that the daemon is shutting down."""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return

        import html
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        uptime_str = html.escape(cls.get_uptime_str())
        safe_reason = html.escape(str(reason))
        text = (
            f"🛑 <b>AI JOB HUNTER — DAEMON STOPPED</b>\n\n"
            f"⏰ <b>Stopped</b>: <code>{now_str}</code>\n"
            f"⏱ <b>Uptime</b>: <code>{uptime_str}</code>\n"
            f"📊 <b>Session Stats</b>:\n"
            f"  • Scans completed: <code>{cls._total_scans}</code>\n"
            f"  • New jobs found: <code>{cls._total_new_jobs}</code>\n"
            f"  • Applications sent: <code>{cls._total_applied}</code>\n"
            f"🔴 <b>Reason</b>: {safe_reason}"
        )
        await TelegramService.send_raw_message(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode="HTML"
        )

    @classmethod
    async def send_heartbeat(cls, db: Optional[AsyncSession] = None):
        """Send periodic status heartbeat to Telegram."""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return

        import html
        db_stats = ""
        if db:
            try:
                from app.models import Job, Application
                job_count_res = await db.execute(select(func.count()).select_from(Job))
                total_jobs = job_count_res.scalar() or 0

                app_count_res = await db.execute(select(func.count()).select_from(Application))
                total_apps = app_count_res.scalar() or 0

                applied_count_res = await db.execute(
                    select(func.count()).select_from(Application).where(Application.status == "APPLIED")
                )
                total_applied_db = applied_count_res.scalar() or 0

                db_stats = (
                    f"\n📦 <b>Database Totals</b>:\n"
                    f"  • Jobs tracked: <code>{total_jobs}</code>\n"
                    f"  • Applications: <code>{total_apps}</code> (<code>{total_applied_db}</code> email-sent)\n"
                )
            except Exception as e:
                logger.warning(f"Heartbeat DB query error: {e}")

        error_status = ""
        if cls._consecutive_errors > 0:
            err_msg = html.escape(str(cls._last_error)[:100]) if cls._last_error else "Unknown"
            error_status = f"\n⚠️ <b>Errors</b>: <code>{cls._consecutive_errors}</code> consecutive\n🔍 <b>Last</b>: <code>{err_msg}</code>\n"

        uptime_str = html.escape(cls.get_uptime_str())
        text = (
            f"💓 <b>AI JOB HUNTER — HEARTBEAT</b>\n\n"
            f"✅ <b>Status</b>: Online & Scanning 24/7\n"
            f"⏱ <b>Uptime</b>: <code>{uptime_str}</code>\n"
            f"🔄 <b>Scans this session</b>: <code>{cls._total_scans}</code>\n"
            f"🆕 <b>New jobs found</b>: <code>{cls._total_new_jobs}</code>\n"
            f"📤 <b>Applications sent</b>: <code>{cls._total_applied}</code>"
            f"{db_stats}"
            f"{error_status}"
        )
        await TelegramService.send_raw_message(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode="HTML"
        )

    @classmethod
    async def send_error_alert(cls, error: str, cycle: int):
        """Send critical error alert to Telegram."""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return

        import html
        cls.record_error(error)

        # Only alert on first error or every 5th consecutive error (avoid spam)
        if cls._consecutive_errors == 1 or cls._consecutive_errors % 5 == 0:
            err_msg = html.escape(str(error)[:300])
            uptime_str = html.escape(cls.get_uptime_str())
            text = (
                f"🔴 <b>AI JOB HUNTER — ERROR ALERT</b>\n\n"
                f"❌ <b>Cycle</b>: <code>#{cycle}</code>\n"
                f"🔁 <b>Consecutive Errors</b>: <code>{cls._consecutive_errors}</code>\n"
                f"🔍 <b>Error</b>: <code>{err_msg}</code>\n"
                f"⏱ <b>Uptime</b>: <code>{uptime_str}</code>"
            )
            await TelegramService.send_raw_message(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                text=text,
                parse_mode="HTML"
            )

    @classmethod
    async def send_scan_summary(cls, cycle: int, scanned: int, new_jobs: int, applied: int):
        """Send summary when new jobs/applications occur, or as periodic hourly keep-alive."""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return

        # 12 cycles * 5 min = 1 hour keep-alive confirmation
        is_hourly_keepalive = (cycle > 0 and cycle % 12 == 0)

        # Skip if quiet cycle and not hourly keep-alive
        if new_jobs == 0 and applied == 0 and not is_hourly_keepalive:
            return

        header = f"📊 <b>SCAN CYCLE #{cycle} SUMMARY</b>" if (new_jobs > 0 or applied > 0) else f"💓 <b>HOURLY SCAN RADAR KEEP-ALIVE (#{cycle})</b>"
        text = (
            f"{header}\n\n"
            f"🔍 <b>Scanned</b>: <code>{scanned}</code> jobs across live feeds\n"
            f"🆕 <b>New Jobs Found</b>: <code>{new_jobs}</code>\n"
            f"📤 <b>Applications Dispatched</b>: <code>{applied}</code>\n"
            f"🟢 <b>Health</b>: 24/7 autonomous monitoring active"
        )
        await TelegramService.send_raw_message(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode="HTML"
        )
