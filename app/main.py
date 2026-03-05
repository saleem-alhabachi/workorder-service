# app/main.py
from __future__ import annotations

import time
import uuid
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.infrastructure.database import ensure_database_exists, engine
from app.infrastructure.models import Base
from app.infrastructure.observability import setup_metrics


password = os.getenv("POSTGRES_PASSWORD")
configure_logging(settings.LOG_LEVEL)
logger = structlog.get_logger()


def _get_db_name_from_url() -> str | None:
    from sqlalchemy.engine import make_url
    try:
        url = make_url(settings.DATABASE_URL)
        return url.database or None
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await ensure_database_exists()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        err_msg = str(e).lower()
        if "does not exist" in err_msg or "invalid_catalog_name" in err_msg:
            db_name = _get_db_name_from_url() or "workorder"
            raise RuntimeError(
                f"Database '{db_name}' does not exist. Create it with:\n"
                f"  sudo -u postgres psql -c \"CREATE DATABASE {db_name};\"\n"
                f"Or (if you have postgres password):\n"
                f"  PGPASSWORD={password} psql -U postgres -h localhost -c \"CREATE DATABASE {db_name};\""
            ) from e
        raise
    yield
    await engine.dispose()


app = FastAPI(title="Work Orders API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "db": "disconnected"},
        )


setup_metrics(app)
app.include_router(api_router, prefix="/api")
