"""
AI Job Hunter — 24/7 Autonomous Background Job Hunter Daemon
Periodically scans global job feeds (ReliefWeb, RemoteOK, UN Jobs, Devex, Visa Sponsorship Boards),
evaluates candidate fit, automatically applies to high-match roles via Gmail with CV attached,
and delivers instant receipts to David on Telegram.
"""

import asyncio
import logging
from app.db.session import session_factory
from app.api.routes.jobs import trigger_job_scan

logger = logging.getLogger(__name__)

# Frequency in seconds (e.g., 3600 = 1 hour)
SCAN_INTERVAL_SECONDS = 3600


async def autonomous_job_hunter_worker():
    """Background loop that continuously sweeps global feeds and auto-applies."""
    logger.info("🚀 Autonomous Job Hunter Daemon started — running 24/7 global sweep.")
    # Initial brief delay to let API boot cleanly
    await asyncio.sleep(10)

    while True:
        try:
            logger.info("🔍 [Autonomous Daemon] Starting scheduled global job scan & auto-apply cycle...")
            async with session_factory() as db:
                result = await trigger_job_scan(db=db)
                logger.info(f"✅ [Autonomous Daemon] Cycle complete: {result.get('scanned_count', 0)} scanned, {result.get('new_jobs_added', 0)} new, {result.get('auto_applied_count', 0)} auto-applied.")
        except asyncio.CancelledError:
            logger.info("Autonomous Job Hunter Daemon shutting down.")
            break
        except Exception as e:
            logger.error(f"❌ [Autonomous Daemon] Error during cycle: {e}")

        # Sleep until next scan interval
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
