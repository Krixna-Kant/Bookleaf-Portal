from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db
from app.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AppError("UNAUTHORIZED", "Missing or invalid authorization header", 401)
    try:
        payload = decode_token(creds.credentials)
    except InvalidTokenError:
        raise AppError("UNAUTHORIZED", "Invalid or expired token", 401) from None
    if payload.get("type") != "access":
        raise AppError("UNAUTHORIZED", "Access token required", 401)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError("UNAUTHORIZED", "Invalid token subject", 401)
    user = db.scalar(select(User).where(User.id == int(user_id)))
    if user is None:
        raise AppError("UNAUTHORIZED", "Account no longer exists", 401)
    return user


def require_author(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.AUTHOR:
        raise AppError("FORBIDDEN", "Author access required", 403)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise AppError("FORBIDDEN", "Admin access required", 403)
    return user
