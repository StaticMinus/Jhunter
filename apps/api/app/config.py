"""
AI Job Hunter — Application Configuration
Pydantic BaseSettings for type-safe, env-driven configuration.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../jhunter.db")).replace("\\", "/")


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ─── Application ───
    app_name: str = "AI Job Hunter"
    app_version: str = "0.1.0"
    debug: bool = False

    # ─── Database ───
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}",
        description="Async database connection string (SQLite for dev, Postgres for prod)",
    )

    # ─── Auth / JWT ───
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32",
        description="JWT signing secret",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # ─── Google OAuth2 ───
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    gmail_refresh_token: str = ""

    # ─── Gemini AI ───
    gemini_api_key: str = ""

    # ─── Telegram Bot ───
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ─── Candidate Context & CV Defaults ───
    default_candidate_email: str = "davidolagbenro35@gmail.com"
    cv_pdf_path: str = "cv_david_ict_specialist.pdf"
    cv_filename: str = "Cv_David_ICT_Specialist.pdf"

    # ─── Daemon / Scheduler ───
    scan_interval_seconds: int = 300  # 5 minutes between scans
    heartbeat_interval_hours: int = 6  # Telegram heartbeat every 6 hours
    max_consecutive_errors: int = 20  # Max errors before extended backoff

    # ─── CORS ───
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": (".env", "apps/api/.env"), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
