from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.db.session import SessionLocal
from app.core.security import verify_token, User

bearer = HTTPBearer(auto_error=False)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        return verify_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

def require_role(required: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if required == "viewer":
            return user
        if required == "editor" and user.role != "editor":
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _dep
