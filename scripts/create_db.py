#!/usr/bin/env python3
"""Create the app database if it does not exist. Uses DATABASE_URL from .env.
Run with a user that can create databases (e.g. postgres). If it fails, run the printed command manually.
"""
import asyncio
import sys

# Load .env and app settings
sys.path.insert(0, ".")
from app.core.config import settings
from sqlalchemy.engine import make_url


async def main() -> None:
    raw = settings.DATABASE_URL
    if "postgresql" not in raw:
        print("DATABASE_URL is not PostgreSQL. Nothing to create.")
        return
    url = make_url(raw)
    db_name = url.database
    if not db_name:
        print("No database name in DATABASE_URL.")
        return

    try:
        import asyncpg
    except ImportError:
        print("Install asyncpg: pip install asyncpg")
        return

    # Connect to default 'postgres' database
    conn = await asyncpg.connect(
        host=url.host or "localhost",
        port=url.port or 5432,
        user=url.username or "postgres",
        password=url.password or "",
        database="postgres",
    )
    try:
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Created database: {db_name}")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f"Database already exists: {db_name}")
    except Exception as e:
        print(f"Failed: {e}")
        print("\nCreate the database manually (use postgres user or sudo):")
        print(f'  sudo -u postgres psql -c "CREATE DATABASE {db_name};"')
        print(f"  or: PGPASSWORD=... psql -U postgres -h localhost -c \"CREATE DATABASE {db_name};\"")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
