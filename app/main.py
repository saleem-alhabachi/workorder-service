import time
import uuid
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes_workorders import router as workorders_router
from app.infrastructure.db.session import engine
from app.infrastructure.db.sqlalchemy_models import Base
from app.infrastructure.observability.metrics import REQUESTS_TOTAL, REQUEST_LATENCY

configure_logging(settings.log_level)
log = logging.getLogger("app")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    log.info("startup_complete", extra={"request_id": "-"})

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()
    path = request.url.path
    method = request.method
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.time() - start
        status_code = getattr(response, "status_code", 500)
        REQUESTS_TOTAL.labels(method=method, path=path, status=str(status_code)).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
        log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status": status_code,
                "duration_ms": int(duration * 1000),
            },
        )

@app.get("/health/live")
def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
def health_ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return Response(content='{"status":"not_ready"}', media_type="application/json", status_code=503)

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

app.include_router(workorders_router)
