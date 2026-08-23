"""
Authentication and multi-tenant workspace service.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, Workspace, UserSession
from app.core.security import SecurityUtils
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles user registration, password verification, workspace creation, and session lifecycle.
    """

    @staticmethod
    def register_user(
        db: Session,
        full_name: str,
        organization: str,
        email: str,
        password: str,
    ) -> Tuple[User, Workspace, UserSession]:
        """
        Creates a new User, associates an initial Workspace, and generates an active UserSession.
        """
        normalized_email = SecurityUtils.normalize_email(email)

        # Check existing user
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        hashed_password = SecurityUtils.hash_password(password)

        user = User(
            full_name=full_name.strip(),
            organization=organization.strip(),
            email=normalized_email,
            password_hash=hashed_password,
            role="owner",
            is_active=True,
        )
        db.add(user)
        db.flush()

        workspace = Workspace(
            name=f"{organization.strip()} Workspace",
            owner_id=user.id,
        )
        db.add(workspace)
        db.flush()

        # Create session
        session = AuthService.create_session(db=db, user_id=user.id)
        db.commit()
        db.refresh(user)
        db.refresh(workspace)
        db.refresh(session)

        return user, workspace, session

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> Tuple[User, Workspace, UserSession]:
        """
        Validates credentials and returns User, default Workspace, and new Session.
        """
        normalized_email = SecurityUtils.normalize_email(email)
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not SecurityUtils.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )

        # Retrieve default workspace or create if missing
        workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
        if not workspace:
            workspace = Workspace(
                name=f"{user.organization} Workspace",
                owner_id=user.id,
            )
            db.add(workspace)
            db.flush()

        session = AuthService.create_session(db=db, user_id=user.id)
        db.commit()
        db.refresh(user)
        db.refresh(workspace)
        db.refresh(session)

        return user, workspace, session

    @staticmethod
    def create_session(db: Session, user_id: uuid.UUID) -> UserSession:
        """
        Creates a new server-side session token with expiration timestamp.
        """
        token = SecurityUtils.generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRE_HOURS)

        session = UserSession(
            user_id=user_id,
            session_token=token,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(session)
        db.flush()
        return session

    @staticmethod
    def validate_session(db: Session, session_token: str) -> Optional[Tuple[User, Workspace]]:
        """
        Validates an active session token and returns the authenticated User and Workspace.
        """
        if not session_token:
            return None

        session = (
            db.query(UserSession)
            .filter(
                UserSession.session_token == session_token,
                UserSession.is_revoked.is_(False),
            )
            .first()
        )

        if not session:
            return None

        # Check expiration
        now = datetime.now(timezone.utc)
        if session.expires_at.tzinfo is None:
            # Handle naive datetime from DB
            session_exp = session.expires_at.replace(tzinfo=timezone.utc)
        else:
            session_exp = session.expires_at

        if session_exp < now:
            session.is_revoked = True
            db.commit()
            return None

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            return None

        workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
        if not workspace:
            workspace = Workspace(
                name=f"{user.organization} Workspace",
                owner_id=user.id,
            )
            db.add(workspace)
            db.commit()
            db.refresh(workspace)

        return user, workspace

    @staticmethod
    def revoke_session(db: Session, session_token: str) -> bool:
        """
        Revokes an active session token (sign out).
        """
        if not session_token:
            return False

        session = (
            db.query(UserSession)
            .filter(UserSession.session_token == session_token)
            .first()
        )
        if session:
            session.is_revoked = True
            db.commit()
            return True
        return False
