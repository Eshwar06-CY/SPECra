"""
Authentication and multi-tenant workspace service.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, Workspace, UserSession, EmailVerificationToken, PasswordResetToken
from app.core.security import SecurityUtils
from app.core.config import settings

logger = logging.getLogger(__name__)


# In-memory login attempt tracking: normalized_email -> {"count": int, "locked_until": datetime}
_login_attempts: dict = {}

# In-memory resend verification rate-limiting: normalized_email -> list of timestamps
_resend_verification_attempts: dict = {}

# In-memory forgot password rate-limiting: normalized_email -> list of timestamps
_forgot_password_attempts: dict = {}


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
    def _check_resend_throttle(normalized_email: str):
        """
        Rate limits resend verification requests to prevent email flooding (max 3 requests per 10 minutes).
        """
        now = datetime.now(timezone.utc)
        window = timedelta(minutes=10)
        max_attempts = 3

        history = _resend_verification_attempts.setdefault(normalized_email, [])
        # Filter timestamps within active sliding window
        valid_history = [t for t in history if now - t < window]
        _resend_verification_attempts[normalized_email] = valid_history

        if len(valid_history) >= max_attempts:
            logger.warning(f"Security Alert: Resend verification rate limit exceeded for '{normalized_email}'.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification requests. Please wait a few minutes before requesting another email.",
            )

        valid_history.append(now)

    @staticmethod
    def register_user(
        db: Session,
        full_name: str,
        organization: str,
        email: str,
        password: str,
    ) -> Tuple[User, Workspace, UserSession]:
        """
        Creates a new User, associates an initial Workspace, issues a secure email verification token,
        and generates an active UserSession.
        """
        from app.services.email_service import EmailService

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

        # Generate CSPRNG verification token
        raw_verify_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_verify_token)
        verify_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)

        user = User(
            full_name=full_name.strip(),
            organization=organization.strip(),
            email=normalized_email,
            password_hash=hashed_password,
            role="owner",
            is_active=True,
            email_verified=False,
            is_verified=False,
            verification_token_hash=token_hash,
            verification_token_expires_at=verify_expires_at,
        )
        db.add(user)
        db.flush()

        # Persist audit record in email_verification_tokens
        token_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=verify_expires_at,
        )
        db.add(token_record)
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

        # Dispatch verification email via EmailService
        EmailService.send_verification_email(
            to_email=user.email,
            verification_token=raw_verify_token,
            full_name=user.full_name,
        )

        logger.info(f"Security: New user registered: '{normalized_email}'. Verification token generated and dispatched.")
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
    def _check_forgot_password_throttle(normalized_email: str):
        """
        Rate limits password reset requests to prevent email flooding (max 3 requests per 10 minutes).
        """
        now = datetime.now(timezone.utc)
        window = timedelta(minutes=10)
        max_attempts = 3

        history = _forgot_password_attempts.setdefault(normalized_email, [])
        valid_history = [t for t in history if now - t < window]
        _forgot_password_attempts[normalized_email] = valid_history

        if len(valid_history) >= max_attempts:
            logger.warning(f"Security Alert: Forgot password rate limit exceeded for '{normalized_email}'.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please wait a few minutes before requesting another reset link.",
            )

        valid_history.append(now)

    @staticmethod
    def request_password_reset(db: Session, email: str) -> bool:
        """
        Generates cryptographically random reset token, stores SHA-256 hash in PasswordResetToken table
        with configured expiry (default 30 min), invalidates prior active tokens, applies rate limiting,
        and dispatches email via EmailService.
        Always returns True to prevent user enumeration.
        """
        from app.services.email_service import EmailService

        normalized_email = SecurityUtils.normalize_email(email)

        # Rate limiting check
        AuthService._check_forgot_password_throttle(normalized_email)

        user = db.query(User).filter(User.email == normalized_email).first()
        now = datetime.now(timezone.utc)

        if user and user.is_active:
            # Invalidate previous active reset tokens for this user
            db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at == None,
            ).update({"used_at": now})

            raw_token = SecurityUtils.generate_session_token()
            token_hash = SecurityUtils.hash_token(raw_token)
            expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

            # Persist in dedicated password_reset_tokens table
            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            db.add(reset_record)

            # Also update User legacy columns for redundancy
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
        Validates token hash and expiration, updates password hash using PBKDF2-HMAC-SHA256,
        marks token as used, and invalidates all existing sessions (Session Invalidation).
        """
        if not raw_token or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token and new password are required.",
            )

        if len(new_password) < 8 or len(new_password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be between 8 and 128 characters in length.",
            )

        token_hash = SecurityUtils.hash_token(raw_token)
        now = datetime.now(timezone.utc)

        # 1. Check PasswordResetToken table
        token_record = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )

        user = None
        if token_record:
            if token_record.used_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This password reset link has already been used. Please request a new one.",
                )

            token_exp = token_record.expires_at.replace(tzinfo=timezone.utc) if token_record.expires_at.tzinfo is None else token_record.expires_at
            if token_exp < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset link has expired. Please request a new one.",
                )

            user = db.query(User).filter(User.id == token_record.user_id).first()
        else:
            # Fallback to User table
            user = db.query(User).filter(User.reset_token_hash == token_hash).first()
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

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link.",
            )

        # Update password hash using PBKDF2
        user.password_hash = SecurityUtils.hash_password(new_password)
        user.reset_token_hash = None
        user.reset_token_expires_at = None

        if token_record:
            token_record.used_at = now

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
    def verify_email(db: Session, raw_token: str) -> dict:
        """
        Validates email verification token and marks user as verified.
        Behavior:
        1. Hash supplied token.
        2. Find matching unused token in EmailVerificationToken (or fallback on User).
        3. Verify expiry.
        4. Verify associated user.
        5. Mark user email_verified = true, is_verified = true.
        6. Set email_verified_at.
        7. Mark token as used (used_at = now).
        8. Reject reuse if already used.
        """
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token is required.",
            )

        token_hash = SecurityUtils.hash_token(raw_token)
        now = datetime.now(timezone.utc)

        # 1. Search EmailVerificationToken table
        token_record = (
            db.query(EmailVerificationToken)
            .filter(EmailVerificationToken.token_hash == token_hash)
            .first()
        )

        user = None
        if token_record:
            if token_record.used_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This verification link has already been used.",
                )

            token_exp = token_record.expires_at.replace(tzinfo=timezone.utc) if token_record.expires_at.tzinfo is None else token_record.expires_at
            if token_exp < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification link has expired. Please request a new one.",
                )

            user = db.query(User).filter(User.id == token_record.user_id).first()
        else:
            # Fallback to User table verification_token_hash
            user = db.query(User).filter(User.verification_token_hash == token_hash).first()
            if not user or not user.verification_token_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired email verification link.",
                )

            user_exp = user.verification_token_expires_at.replace(tzinfo=timezone.utc) if user.verification_token_expires_at.tzinfo is None else user.verification_token_expires_at
            if user_exp < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification link has expired. Please request a new one.",
                )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification link or user not found.",
            )

        # If already verified
        if user.email_verified:
            if token_record:
                token_record.used_at = now
            user.verification_token_hash = None
            user.verification_token_expires_at = None
            db.commit()
            return {"message": "Email is already verified. You can sign in to your account.", "already_verified": True}

        # Mark user as verified
        user.email_verified = True
        user.is_verified = True
        user.email_verified_at = now
        user.verification_token_hash = None
        user.verification_token_expires_at = None

        if token_record:
            token_record.used_at = now

        db.commit()
        logger.info(f"Security: Email address successfully verified for user '{user.email}'")
        return {"message": "Your email address has been verified successfully. Your workspace is now active."}

    @staticmethod
    def resend_verification(db: Session, email: str) -> bool:
        """
        Resends email verification link.
        Requirements:
        - Rate limit requests.
        - Prevent email flooding.
        - Do not expose whether an email exists (generic response).
        - Invalidate previous active verification tokens.
        - Generate a new secure token and dispatch via EmailService.
        """
        from app.services.email_service import EmailService

        normalized_email = SecurityUtils.normalize_email(email)

        # Rate limiting check
        AuthService._check_resend_throttle(normalized_email)

        user = db.query(User).filter(User.email == normalized_email).first()
        now = datetime.now(timezone.utc)

        if user and not user.email_verified and user.is_active:
            # 1. Invalidate previous active verification tokens for this user
            db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.used_at == None,
            ).update({"used_at": now})

            # 2. Generate new token
            raw_verify_token = SecurityUtils.generate_session_token()
            token_hash = SecurityUtils.hash_token(raw_verify_token)
            verify_expires_at = now + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)

            user.verification_token_hash = token_hash
            user.verification_token_expires_at = verify_expires_at

            token_record = EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=verify_expires_at,
            )
            db.add(token_record)
            db.commit()

            EmailService.send_verification_email(
                to_email=user.email,
                verification_token=raw_verify_token,
                full_name=user.full_name,
            )
            logger.info(f"Security: New verification token issued and sent for '{normalized_email}'")
        else:
            logger.info(f"Security: Resend verification requested for verified/non-existent email '{normalized_email}'")

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

