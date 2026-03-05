# app/infrastructure/observability.py
from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    """Add Prometheus metrics endpoint at /metrics."""
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
