"""
AI Job Hunter — Application Configuration
Pydantic BaseSettings for type-safe, env-driven configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ─── Application ───
    app_name: str = "AI Job Hunter"
    app_version: str = "0.1.0"
    debug: bool = False

    # ─── Database ───
    database_url: str = Field(
        default="sqlite+aiosqlite:///./jhunter.db",
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

    # ─── Gemini AI ───
    gemini_api_key: str = ""

    # ─── Telegram Bot ───
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ─── CORS ───
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": (".env", "apps/api/.env"), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
