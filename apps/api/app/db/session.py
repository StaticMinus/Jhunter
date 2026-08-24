"""
AI Job Hunter — Async SQLAlchemy Session Factory
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine_kwargs = {"echo": settings.debug}
if "sqlite" in settings.database_url:
    engine_kwargs["connect_args"] = {"timeout": 30.0}
else:
    engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)


session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def init_db() -> None:
    """Create all tables (dev convenience; use Alembic in production)."""
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            from sqlalchemy import text
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA busy_timeout=30000;"))
        await conn.run_sync(Base.metadata.create_all)



async def close_db() -> None:
    """Dispose of the engine connection pool."""
    await engine.dispose()
