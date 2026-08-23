"""
API Router for User Authentication, Workspace Session Management, and Profile Retrieval.
"""
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    AuthResponse,
)
from app.models.user import User, Workspace
from app.services.auth_service import AuthService
from app.api.deps import (
    get_current_auth,
    get_current_user,
    get_current_workspace,
    get_session_token_from_request,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def set_session_cookie(response: Response, session_token: str):
    """
    Sets secure HttpOnly session cookie.
    """
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response):
    """
    Clears session cookie upon logout.
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and create private workspace",
)
def register(
    data: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint.
    Creates account with PBKDF2 hashed password, initial workspace, and active HttpOnly session.
    """
    user, workspace, session = AuthService.register_user(
        db=db,
        full_name=data.full_name,
        organization=data.organization,
        email=data.email,
        password=data.password,
    )

    set_session_cookie(response, session.session_token)

    return AuthResponse(
        message="Account created successfully.",
        user=UserProfileResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            organization=user.organization,
            role=user.role,
            workspace_id=workspace.id,
            workspace_name=workspace.name,
            created_at=user.created_at,
        ),
        session_token=session.session_token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user credentials and start session",
)
def login(
    data: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint.
    Validates email and password, creates new active session, sets HttpOnly cookie.
    """
    user, workspace, session = AuthService.authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
    )

    set_session_cookie(response, session.session_token)

    return AuthResponse(
        message="Signed in successfully.",
        user=UserProfileResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            organization=user.organization,
            role=user.role,
            workspace_id=workspace.id,
            workspace_name=workspace.name,
            created_at=user.created_at,
        ),
        session_token=session.session_token,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get profile of authenticated user",
)
def get_me(
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
):
    """
    AUTHENTICATED endpoint.
    Returns currently signed-in user and workspace information.
    """
    user, workspace = auth
    return UserProfileResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        organization=user.organization,
        role=user.role,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        created_at=user.created_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active session and sign out",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    AUTHENTICATED endpoint.
    Revokes the current server session and clears the browser cookie.
    """
    token = get_session_token_from_request(request)
    if token:
        AuthService.revoke_session(db=db, session_token=token)

    clear_session_cookie(response)
    return {"message": "Signed out successfully."}
