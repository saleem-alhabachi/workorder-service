# app/infrastructure/database.py
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infrastructure.models import Base

logger = logging.getLogger(__name__)


def _get_async_url(url: str) -> str:
    """Ensure URL uses asyncpg for PostgreSQL."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def ensure_database_exists() -> None:
    """Create the database if it does not exist (PostgreSQL only).
    On connection failure (e.g. no access to 'postgres' DB), logs and continues
    so startup can succeed when the target database already exists.
    """
    raw = settings.DATABASE_URL
    if "postgresql" not in raw:
        return
    url = make_url(raw)
    db_name = url.database
    if not db_name:
        return
    admin_url = url.set(database="postgres")
    admin_async_url = _get_async_url(str(admin_url))
    admin_engine = create_async_engine(
        admin_async_url, isolation_level="AUTOCOMMIT"
    )
    try:
        async with admin_engine.connect() as conn:
            stmt = text("SELECT 1 FROM pg_database WHERE datname = :name")
            result = await conn.execute(stmt, {"name": db_name})
            if result.scalar() is None:
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    except Exception as e:
        logger.warning(
            "Could not ensure database exists (e.g. no access to 'postgres' or wrong password). "
            "Continuing; app will fail if target DB is missing. Error: %s",
            e,
        )
    finally:
        await admin_engine.dispose()


engine = create_async_engine(
    _get_async_url(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
