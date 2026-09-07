import os
import sys

# Ensure workspace root is in sys.path for worker adapter discovery
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import init_db, close_db
from app.api.routes import auth, candidate, jobs, applications, integrations, notifications


import asyncio
from app.services.scheduler import autonomous_job_hunter_worker
from app.services.health_monitor import HealthMonitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown hooks."""
    try:
        await init_db()
    except Exception as e:
        print(f"Database init warning (will use cross-dialect session): {e}")

    # Launch 24/7 autonomous background job hunter daemon
    bg_task = asyncio.create_task(autonomous_job_hunter_worker())

    yield

    # Graceful shutdown — notify Telegram
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

    try:
        await HealthMonitor.send_shutdown_alert("API server shutting down")
    except Exception:
        pass

    await close_db()



def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Job Hunter API",
        version="0.2.0",
        description="Autonomous Executive Recruitment Intelligence & Application Assistant API — 24/7 Hardened",
        lifespan=lifespan
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router registrations
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(candidate.router, prefix="/api/candidate", tags=["candidate"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
    app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "AI Job Hunter Backend",
            "version": settings.app_version,
            "engine": "FastAPI + SQLAlchemy Async",
            "daemon": "24/7 autonomous scanner active",
            "uptime": HealthMonitor.get_uptime_str(),
            "total_scans": HealthMonitor._total_scans,
            "total_applied": HealthMonitor._total_applied,
            "scan_interval": f"{settings.scan_interval_seconds}s"
        }

    return app


app = create_app()
