# app/api/dependencies.py
from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import User, decode_token
from app.infrastructure.database import get_db
from app.infrastructure.repository import SQLAlchemyWorkOrderRepository
from app.domain.interfaces import WorkOrderRepository

security = HTTPBearer(auto_error=False)


async def get_workorder_repository(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[WorkOrderRepository, None]:
    yield SQLAlchemyWorkOrderRepository(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_viewer(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("viewer", "editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


async def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role != "editor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor role required",
        )
    return user
