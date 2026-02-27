from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import jwt
from jwt import PyJWTError
from app.core.config import settings

@dataclass(frozen=True)
class User:
    sub: str
    role: str  # viewer | editor

def create_token(user_id: str, role: str = "editor") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        return User(sub=str(payload["sub"]), role=str(payload.get("role", "viewer")))
    except PyJWTError as e:
        raise ValueError("Invalid token") from e
