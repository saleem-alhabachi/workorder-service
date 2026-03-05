# app/core/security.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


@dataclass(frozen=True)
class User:
    sub: str
    role: str  # "viewer" | "editor"


def create_access_token(
    subject: str,
    role: str = "viewer",
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        sub = payload.get("sub")
        role = payload.get("role", "viewer")
        if not sub:
            raise ValueError("Missing sub in token")
        if role not in ("viewer", "editor"):
            role = "viewer"
        return User(sub=str(sub), role=role)
    except JWTError as e:
        raise ValueError("Invalid token") from e
