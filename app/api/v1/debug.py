# app/api/v1/debug.py
from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute

from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/routes")
async def list_routes(request: Request) -> list[dict[str, Any]]:
    routes = []
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods),
                "summary": route.summary or route.description or "",
            })
    return routes


@router.post("/token")
async def generate_token(role: str = "viewer") -> dict[str, str]:
    if role not in ("viewer", "editor"):
        role = "viewer"
    token = create_access_token(subject=f"debug-{role}", role=role)
    return {"token": token, "role": role}


@router.post("/run-tests")
async def run_integration_tests() -> dict[str, Any]:
    # Run the scripts/test_routes.py script
    # We assume the server is running on localhost:8000 or as configured
    process = await asyncio.create_subprocess_exec(
        "python3", "scripts/test_routes.py",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": "."}
    )
    stdout, stderr = await process.communicate()
    
    return {
        "exit_code": process.returncode,
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
    }


@router.post("/run-pytest")
async def run_unit_tests() -> dict[str, Any]:
    process = await asyncio.create_subprocess_exec(
        "pytest", "tests/", "-v", "--color=no",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": ".", "DATABASE_URL": "sqlite+aiosqlite:///:memory:"}
    )
    stdout, stderr = await process.communicate()
    
    return {
        "exit_code": process.returncode,
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
    }
