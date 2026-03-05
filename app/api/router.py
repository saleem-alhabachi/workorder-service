# app/api/router.py
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import workorders as v1_workorders

api_router = APIRouter()
api_router.include_router(v1_workorders.router, prefix="/v1")
