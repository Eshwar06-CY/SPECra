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
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    SessionInfoResponse,
    DeleteAccountRequest,
)
from app.models.user import User, Workspace, UserSession
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
            is_verified=user.is_verified,
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
        is_verified=user.is_verified,
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


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset email",
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint.
    Issues a hashed password-reset token and dispatches reset instructions.
    Always returns generic success to protect against user enumeration.
    """
    AuthService.request_password_reset(db=db, email=data.email)
    return {
        "message": "If an account matches that email address, password reset instructions have been sent."
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using valid token",
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint.
    Validates token, updates password hash, clears token, and invalidates all prior sessions.
    """
    AuthService.reset_password(db=db, raw_token=data.token, new_password=data.new_password)
    return {"message": "Your password has been reset successfully. You can now sign in with your new credentials."}


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password for authenticated user",
)
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """
    AUTHENTICATED endpoint.
    Verifies existing password, hashes new password, updates record, and revokes other sessions.
    """
    user, _ = auth
    current_token = get_session_token_from_request(request)
    AuthService.change_password(
        db=db,
        user=user,
        current_password=data.current_password,
        new_password=data.new_password,
        current_token=current_token,
    )
    return {"message": "Password changed successfully."}


@router.get(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address with token",
)
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint.
    Validates email verification token and marks user account as verified.
    """
    AuthService.verify_email(db=db, raw_token=token)
    return {"message": "Your email address has been verified successfully."}


@router.get(
    "/sessions",
    response_model=list[SessionInfoResponse],
    summary="List active sessions for authenticated user",
)
def get_sessions(
    request: Request,
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """
    AUTHENTICATED endpoint.
    Lists active sessions for the current user without exposing raw session tokens.
    """
    user, _ = auth
    current_token = get_session_token_from_request(request)
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_revoked.is_(False))
        .order_by(UserSession.created_at.desc())
        .all()
    )

    return [
        SessionInfoResponse(
            id=s.id,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current=(s.session_token == current_token),
        )
        for s in sessions
    ]


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke specific user session",
)
def revoke_specific_session(
    session_id: str,
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """
    AUTHENTICATED endpoint.
    Revokes a specific session belonging to the authenticated user.
    """
    import uuid
    user, _ = auth
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID format.")

    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_uuid, UserSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    session.is_revoked = True
    db.commit()
    return {"message": "Session revoked successfully."}


@router.post(
    "/delete-account",
    status_code=status.HTTP_200_OK,
    summary="Permanently delete user account and workspace",
)
def delete_account(
    data: DeleteAccountRequest,
    response: Response,
    auth: Tuple[User, Workspace] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """
    AUTHENTICATED endpoint.
    Permanently deletes user account, cascade-deletes workspaces and datasets upon confirmation.
    """
    user, _ = auth
    AuthService.delete_account(
        db=db,
        user=user,
        password=data.password,
        confirm_text=data.confirm_text,
    )
    clear_session_cookie(response)
    return {"message": "Your account has been deleted permanently."}

