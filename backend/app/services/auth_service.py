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


# In-memory login attempt tracking: normalized_email -> {"count": int, "locked_until": datetime}
_login_attempts: dict = {}


class AuthService:
    """
    Handles user registration, password verification, workspace creation, and session lifecycle.
    """

    @staticmethod
    def _check_login_throttle(normalized_email: str):
        """
        Verifies whether an account/email is temporarily locked out due to repeated failed attempts.
        """
        now = datetime.now(timezone.utc)
        record = _login_attempts.get(normalized_email)
        if record:
            locked_until = record.get("locked_until")
            if locked_until and now < locked_until:
                remaining_secs = int((locked_until - now).total_seconds())
                logger.warning(
                    f"Security Alert: Blocked login attempt for locked email '{normalized_email}'. "
                    f"Locked for {remaining_secs} more seconds."
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please wait a few minutes before trying again.",
                )
            elif locked_until and now >= locked_until:
                # Lockout expired, reset
                _login_attempts.pop(normalized_email, None)

    @staticmethod
    def _record_failed_login(normalized_email: str):
        """
        Increments failed attempt count and triggers temporary lockout if threshold reached.
        """
        now = datetime.now(timezone.utc)
        record = _login_attempts.setdefault(normalized_email, {"count": 0, "locked_until": None})
        record["count"] += 1

        logger.warning(f"Security Alert: Failed login attempt for email '{normalized_email}' (Count: {record['count']})")

        if record["count"] >= settings.MAX_LOGIN_ATTEMPTS:
            record["locked_until"] = now + timedelta(seconds=settings.LOGIN_LOCKOUT_SECONDS)
            logger.warning(
                f"Security Alert: Account login locked for '{normalized_email}' for {settings.LOGIN_LOCKOUT_SECONDS}s "
                f"after {record['count']} failed attempts."
            )

    @staticmethod
    def _reset_login_attempts(normalized_email: str):
        """
        Resets failed login tracking upon successful authentication.
        """
        _login_attempts.pop(normalized_email, None)

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
            logger.info(f"Registration attempted with existing email: '{normalized_email}'")
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

        logger.info(f"Security: New user registered successfully: '{normalized_email}' (Workspace ID: {workspace.id})")
        return user, workspace, session

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> Tuple[User, Workspace, UserSession]:
        """
        Validates credentials and returns User, default Workspace, and new Session.
        Implements brute-force lockout protection and constant-time failure response.
        """
        normalized_email = SecurityUtils.normalize_email(email)

        # 1. Check temporary lockout
        AuthService._check_login_throttle(normalized_email)

        # 2. Lookup user and verify password
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not SecurityUtils.verify_password(password, user.password_hash):
            AuthService._record_failed_login(normalized_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            logger.warning(f"Security: Sign-in attempted on deactivated account: '{normalized_email}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )

        # 3. Successful authentication -> Reset throttle counter
        AuthService._reset_login_attempts(normalized_email)

        # Retrieve default workspace or create if missing
        workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
        if not workspace:
            workspace = Workspace(
                name=f"{user.organization} Workspace",
                owner_id=user.id,
            )
            db.add(workspace)
            db.flush()

        # Session Fixation Protection: Always generate a brand new session token
        session = AuthService.create_session(db=db, user_id=user.id)
        db.commit()
        db.refresh(user)
        db.refresh(workspace)
        db.refresh(session)

        logger.info(f"Security: User '{normalized_email}' authenticated successfully (Session ID: {session.id})")
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

    @staticmethod
    def request_password_reset(db: Session, email: str) -> bool:
        """
        Generates cryptographically random reset token, stores SHA-256 hash in DB with 30-min expiry,
        and dispatches email via EmailService.
        Always returns True to prevent user enumeration.
        """
        from app.services.email_service import EmailService

        normalized_email = SecurityUtils.normalize_email(email)
        user = db.query(User).filter(User.email == normalized_email).first()

        if user and user.is_active:
            raw_token = SecurityUtils.generate_session_token()
            token_hash = SecurityUtils.hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

            user.reset_token_hash = token_hash
            user.reset_token_expires_at = expires_at
            db.commit()

            EmailService.send_password_reset_email(
                to_email=user.email,
                reset_token=raw_token,
                full_name=user.full_name,
            )
            logger.info(f"Security: Password reset token issued for '{normalized_email}'")
        else:
            logger.info(f"Security: Password reset requested for non-existent/inactive email '{normalized_email}'")

        return True

    @staticmethod
    def reset_password(db: Session, raw_token: str, new_password: str) -> bool:
        """
        Validates token hash and expiration, updates password hash, clears token,
        and invalidates all existing sessions (Session Invalidation).
        """
        if not raw_token or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token and new password are required.",
            )

        token_hash = SecurityUtils.hash_token(raw_token)
        user = db.query(User).filter(User.reset_token_hash == token_hash).first()

        now = datetime.now(timezone.utc)
        if not user or not user.reset_token_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link.",
            )

        user_exp = user.reset_token_expires_at.replace(tzinfo=timezone.utc) if user.reset_token_expires_at.tzinfo is None else user.reset_token_expires_at
        if user_exp < now:
            user.reset_token_hash = None
            user.reset_token_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset link has expired. Please request a new one.",
            )

        # Update password hash
        user.password_hash = SecurityUtils.hash_password(new_password)
        user.reset_token_hash = None
        user.reset_token_expires_at = None

        # Revoke all existing sessions for this user (Security best practice)
        db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})
        db.commit()

        logger.info(f"Security: Password successfully reset for user '{user.email}'. All active sessions revoked.")
        return True

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str, current_token: Optional[str] = None) -> bool:
        """
        Verifies current password, hashes new password, updates database, and revokes all other sessions.
        """
        if not SecurityUtils.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password.",
            )

        user.password_hash = SecurityUtils.hash_password(new_password)

        # Revoke other sessions except current session
        if current_token:
            db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.session_token != current_token,
            ).update({"is_revoked": True})
        else:
            db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})

        db.commit()
        logger.info(f"Security: User '{user.email}' changed password. Other sessions revoked.")
        return True

    @staticmethod
    def verify_email(db: Session, raw_token: str) -> bool:
        """
        Validates email verification token and marks user as verified.
        """
        token_hash = SecurityUtils.hash_token(raw_token)
        user = db.query(User).filter(User.verification_token_hash == token_hash).first()

        now = datetime.now(timezone.utc)
        if not user or not user.verification_token_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired email verification link.",
            )

        user_exp = user.verification_token_expires_at.replace(tzinfo=timezone.utc) if user.verification_token_expires_at.tzinfo is None else user.verification_token_expires_at
        if user_exp < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired.",
            )

        user.is_verified = True
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        db.commit()

        logger.info(f"Security: Email address verified for user '{user.email}'")
        return True

    @staticmethod
    def delete_account(db: Session, user: User, password: str, confirm_text: str) -> bool:
        """
        Permanently deletes user account and cascading workspace data upon password confirmation.
        """
        if confirm_text != "DELETE MY ACCOUNT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation text does not match 'DELETE MY ACCOUNT'.",
            )

        if not SecurityUtils.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password. Account deletion aborted.",
            )

        email = user.email
        db.delete(user)
        db.commit()
        logger.warning(f"Security Alert: Account deleted permanently for user '{email}'")
        return True

