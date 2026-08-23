"""
FastAPI dependency injection for authentication and multi-tenant authorization.
"""
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, Workspace
from app.services.auth_service import AuthService


def get_session_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts session token: Authorization Bearer header first (API/clients), then HttpOnly cookie (browsers).
    """
    # 1. Check Authorization Bearer Header
    auth_hdr = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_hdr and isinstance(auth_hdr, str) and auth_hdr.startswith("Bearer "):
        return auth_hdr.split("Bearer ", 1)[1].strip()

    # 2. Check HttpOnly Cookie
    cookie_token = request.cookies.get(settings.COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def get_current_auth(
    request: Request,
    db: Session = Depends(get_db),
) -> Tuple[User, Workspace]:
    """
    AUTHENTICATED Dependency.
    Rejects unauthenticated requests with HTTP 401.
    Returns (User, Workspace) tuple for tenant isolation.
    """
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
        )

    auth_data = AuthService.validate_session(db=db, session_token=token)
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
        )

    return auth_data


def get_current_user(
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
) -> User:
    """
    Returns authenticated User.
    """
    return auth[0]


def get_current_workspace(
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
) -> Workspace:
    """
    Returns authenticated Workspace for strict tenant boundary enforcement.
    """
    return auth[1]


def get_optional_auth(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[Tuple[User, Workspace]]:
    """
    OPTIONAL Dependency for public or backwards-compatible endpoints.
    """
    token = get_session_token_from_request(request)
    if not token:
        return None
    return AuthService.validate_session(db=db, session_token=token)
