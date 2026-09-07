"""
AI Job Hunter — 24/7 Autonomous Background Job Hunter Daemon
Periodically scans global job feeds (ReliefWeb, RemoteOK, UN Jobs, Devex, Visa Sponsorship Boards),
evaluates candidate fit, automatically applies to high-match roles via Gmail with CV attached,
and delivers instant receipts to David on Telegram.

Hardened for 24/7 operation with:
- Configurable scan intervals (default 5 minutes)
- Exponential backoff on consecutive failures
- Periodic heartbeat notifications via Telegram
- Scan run tracking in the database
- Proactive Google OAuth token refresh
- Rotating pagination to discover fresh jobs
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select

from app.db.session import session_factory
from app.api.routes.jobs import trigger_job_scan
from app.config import settings
from app.services.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


async def _refresh_google_token_if_needed(db):
    """Proactively refresh Google OAuth tokens for all candidates before expiry."""
    from app.models import User
    from app.services.gmail_service import GmailService

    try:
        user_res = await db.execute(select(User).where(User.google_tokens_encrypted.is_not(None)))
        users = user_res.scalars().all()
        for user in users:
            if not user.google_tokens_encrypted:
                continue

            try:
                tokens = json.loads(user.google_tokens_encrypted)
                refresh_token = tokens.get("refresh_token")
                client_id = tokens.get("client_id", settings.google_client_id)
                client_secret = tokens.get("client_secret", settings.google_client_secret)

                # Skip client_secret.json blobs — these are NOT OAuth tokens
                if "web" in tokens and "access_token" not in tokens:
                    logger.debug(f"Skipping token refresh for {user.name} — stored blob is client_secret.json, not OAuth tokens.")
                    continue

                if not refresh_token:
                    continue

                # Always try to refresh — access tokens expire every hour
                new_access = await GmailService.refresh_access_token(
                    refresh_token,
                    client_id=client_id,
                    client_secret=client_secret
                )
                if new_access:
                    tokens["access_token"] = new_access
                    user.google_tokens_encrypted = json.dumps(tokens)
                    db.add(user)
                    await db.commit()
                    logger.info(f"✅ Google OAuth access token proactively refreshed for {user.name} ({user.email}).")
                else:
                    logger.warning(f"⚠️ Google token refresh returned None for {user.name} — refresh token may be revoked.")
            except Exception as user_err:
                logger.warning(f"Failed to refresh tokens for user {user.id}: {user_err}")
    except Exception as e:
        logger.warning(f"Token refresh check error (non-fatal): {e}")


async def _record_scan_run(db, scanned: int, new_jobs: int, applied: int, errors: str = None):
    """Record scan cycle to the scan_runs table."""
    from app.models import ScanRun, JobSource

    try:
        # Get or create default source
        src_res = await db.execute(select(JobSource).limit(1))
        source = src_res.scalar_one_or_none()

        scan = ScanRun(
            source_id=source.id if source else None,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status="SUCCESS" if not errors else "ERROR",
            jobs_found=scanned,
            jobs_new=new_jobs,
            error_log=errors
        )
        db.add(scan)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to record scan run: {e}")


def _calculate_backoff(consecutive_errors: int) -> int:
    """Exponential backoff: 5min → 10min → 20min → max 30min."""
    base = settings.scan_interval_seconds
    if consecutive_errors <= 0:
        return base
    backoff = min(base * (2 ** min(consecutive_errors, 4)), 1800)  # Max 30 minutes
    return int(backoff)


async def autonomous_job_hunter_worker():
    """Background loop that continuously sweeps global feeds and auto-applies."""
    logger.info("🚀 Autonomous Job Hunter Daemon started — running 24/7 global sweep.")

    # Send startup notification
    try:
        await HealthMonitor.send_startup_alert()
    except Exception as e:
        logger.warning(f"Startup alert failed: {e}")

    # Initial brief delay to let API boot cleanly
    await asyncio.sleep(10)

    cycle_count = 0
    consecutive_errors = 0
    heartbeat_cycle_trigger = (settings.heartbeat_interval_hours * 3600) // settings.scan_interval_seconds

    while True:
        cycle_count += 1

        try:
            logger.info(f"🔍 [Cycle #{cycle_count}] Starting scheduled global job scan & auto-apply cycle...")

            async with session_factory() as db:
                # Proactively refresh OAuth token every cycle
                await _refresh_google_token_if_needed(db)

                # Run the main scan
                result = await trigger_job_scan(db=db)
                scanned = result.get("scanned_count", 0)
                new_jobs = result.get("new_jobs_added", 0)
                auto_applied = result.get("auto_applied_count", 0)

                logger.info(
                    f"✅ [Cycle #{cycle_count}] Complete: "
                    f"{scanned} scanned, {new_jobs} new, {auto_applied} auto-applied."
                )

                # Record to health monitor
                HealthMonitor.record_scan(scanned, new_jobs, auto_applied)

                # Record scan run in DB
                await _record_scan_run(db, scanned, new_jobs, auto_applied)

                # Send Telegram summary if interesting results
                await HealthMonitor.send_scan_summary(cycle_count, scanned, new_jobs, auto_applied)

                consecutive_errors = 0

                # Periodic heartbeat
                if cycle_count % heartbeat_cycle_trigger == 0:
                    async with session_factory() as hb_db:
                        await HealthMonitor.send_heartbeat(hb_db)

        except asyncio.CancelledError:
            logger.info("Autonomous Job Hunter Daemon shutting down.")
            try:
                await HealthMonitor.send_shutdown_alert("Process cancelled (server shutdown)")
            except Exception:
                pass
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ [Cycle #{cycle_count}] Error during cycle: {e}", exc_info=True)

            # Record error in health monitor
            await HealthMonitor.send_error_alert(str(e), cycle_count)

            # Record failed scan run
            try:
                async with session_factory() as err_db:
                    await _record_scan_run(err_db, 0, 0, 0, errors=str(e)[:500])
            except Exception:
                pass

        # Calculate sleep with backoff on errors
        sleep_seconds = _calculate_backoff(consecutive_errors)
        if consecutive_errors > 0:
            logger.info(f"⏳ Backoff sleep: {sleep_seconds}s (consecutive errors: {consecutive_errors})")
        else:
            logger.info(f"⏳ Next scan in {sleep_seconds}s...")

        await asyncio.sleep(sleep_seconds)
