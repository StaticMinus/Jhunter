"""
AI Job Hunter — Continuous 24/7 Autonomous Daemon (Standalone Runner)
Alternative to running inside FastAPI lifespan.
Can be launched independently: python workers/autonomous_daemon.py
Continuously discovers, deduplicates, matches, and auto-applies to global jobs.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
APPS_API_DIR = os.path.join(ROOT_DIR, "apps", "api")
if APPS_API_DIR not in sys.path:
    sys.path.insert(0, APPS_API_DIR)

from app.db.session import init_db, session_factory
from app.api.routes.jobs import trigger_job_scan
from app.config import settings
from app.services.health_monitor import HealthMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("autonomous_pump")


async def run_daemon(single_run: bool = False):
    logger.info("=" * 65)
    logger.info("🚀 AI JOB HUNTER — CONTINUOUS PUMP DAEMON INITIALIZED")
    logger.info(f"Target: Continuous global discovery & live auto-application")
    logger.info(f"Interval: Every {settings.scan_interval_seconds} seconds")
    logger.info(f"Heartbeat: Every {settings.heartbeat_interval_hours} hours")
    if single_run:
        logger.info("Mode: SINGLE RUN (--once)")
    logger.info("=" * 65)

    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database init warning: {e}")

    # Send startup notification
    try:
        await HealthMonitor.send_startup_alert()
    except Exception as e:
        logger.warning(f"Startup alert failed: {e}")

    cycle_count = 0
    consecutive_errors = 0
    heartbeat_trigger = (settings.heartbeat_interval_hours * 3600) // settings.scan_interval_seconds

    while True:
        cycle_count += 1
        logger.info(f"\n⚡ [Cycle #{cycle_count}] Starting full-spectrum global job sweep & auto-apply...")

        try:
            async with session_factory() as db:
                # Proactive token refresh
                from app.services.scheduler import _refresh_google_token_if_needed
                await _refresh_google_token_if_needed(db)

                result = await trigger_job_scan(db=db)
                scanned = result.get("scanned_count", 0)
                new_jobs = result.get("new_jobs_added", 0)
                auto_applied = result.get("auto_applied_count", 0)

                logger.info(
                    f"🎯 [Cycle #{cycle_count} COMPLETE] "
                    f"Scanned: {scanned} | "
                    f"New Jobs: {new_jobs} | "
                    f"Applications Dispatched: {auto_applied}"
                )

                HealthMonitor.record_scan(scanned, new_jobs, auto_applied)
                from app.services.scheduler import _record_scan_run
                await _record_scan_run(db, scanned, new_jobs, auto_applied)
                await HealthMonitor.send_scan_summary(cycle_count, scanned, new_jobs, auto_applied)
                consecutive_errors = 0

                # Periodic heartbeat
                if cycle_count % heartbeat_trigger == 0:
                    async with session_factory() as hb_db:
                        await HealthMonitor.send_heartbeat(hb_db)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ [Cycle #{cycle_count} ERROR] Error in scan cycle: {e}", exc_info=True)
            await HealthMonitor.send_error_alert(str(e), cycle_count)
            try:
                async with session_factory() as err_db:
                    from app.services.scheduler import _record_scan_run
                    await _record_scan_run(err_db, 0, 0, 0, errors=str(e)[:500])
            except Exception:
                pass

        if single_run:
            logger.info("✅ Single scan run completed successfully. Exiting.")
            break

        # Calculate sleep with backoff
        from app.services.scheduler import _calculate_backoff
        sleep_seconds = _calculate_backoff(consecutive_errors)
        logger.info(f"⏳ Sleeping for {sleep_seconds}s until next sweep cycle...")
        await asyncio.sleep(sleep_seconds)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Job Hunter Autonomous Daemon")
    parser.add_argument("--once", action="store_true", help="Run a single scan & auto-apply cycle, then exit")
    args = parser.parse_args()

    single_run = args.once or os.getenv("SINGLE_RUN", "").lower() in ("true", "1", "yes")

    try:
        asyncio.run(run_daemon(single_run=single_run))
    except KeyboardInterrupt:
        logger.info("Daemon stopped by operator.")
        try:
            asyncio.run(HealthMonitor.send_shutdown_alert("Operator keyboard interrupt"))
        except Exception:
            pass
