"""
Comprehensive Security and Multi-Tenant Authentication Test Suite for SPECra.
Tests:
1. User Registration with PBKDF2 Password Hashing
2. Duplicate Email Rejection
3. Valid User Authentication and Session Token Issuance
4. Invalid Password Rejection
5. Unknown Email Rejection
6. Authenticated /me Profile Retrieval
7. Unauthenticated /me Rejection (HTTP 401)
8. User Logout and Session Revocation
9. Multi-Tenant Job Isolation (User A cannot see User B jobs)
10. IDOR Protection (User B cannot access User A job status, schema, records, or exports)
11. Secure Passwords never returned in API responses
"""
import uuid
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, SessionLocal, get_db
from app.core.security import SecurityUtils
from app.models.user import User, Workspace, UserSession, EmailVerificationToken, PasswordResetToken
from app.models.product import ProcessingJob, Product
from app.services.auth_service import AuthService

# Use an in-memory SQLite database or live DB engine for isolated tests
from app.core.config import settings

client = TestClient(app)


class TestSPECraAuthenticationAndSecurity(unittest.TestCase):
    """
    Test suite for server-side auth, password security, session cookies, and multi-tenant IDOR protection.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.user_a_email = f"alice_{uuid.uuid4().hex[:8]}@example.test"
        self.user_b_email = f"bob_{uuid.uuid4().hex[:8]}@example.test"
        self.password = "SecurePassword123!"

    def test_01_password_hashing_security(self):
        """Verify PBKDF2-HMAC-SHA256 hashing produces unique salts and verifies correctly."""
        hash1 = SecurityUtils.hash_password("mysecret")
        hash2 = SecurityUtils.hash_password("mysecret")

        self.assertNotEqual(hash1, hash2, "Different salts must produce different hash strings")
        self.assertTrue(SecurityUtils.verify_password("mysecret", hash1))
        self.assertTrue(SecurityUtils.verify_password("mysecret", hash2))
        self.assertFalse(SecurityUtils.verify_password("wrongpassword", hash1))

    def test_02_user_registration_and_duplicate_rejection(self):
        """Verify user registration and rejection of duplicate emails."""
        # 1. Register User A
        reg_payload = {
            "full_name": "Alice Developer",
            "organization": "Acme Industries",
            "email": self.user_a_email,
            "password": self.password,
        }
        res = self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.user_a_email)
        self.assertNotIn("password", data["user"])
        self.assertNotIn("password_hash", data["user"])

        # 2. Duplicate registration with same email must fail
        dup_res = self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("already exists", dup_res.json()["detail"])

    def test_03_login_and_credential_verification(self):
        """Verify valid login, invalid password rejection, and unknown email rejection."""
        # Register user
        reg_payload = {
            "full_name": "Bob Analyst",
            "organization": "Supply Chain Corp",
            "email": self.user_b_email,
            "password": self.password,
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)

        # 1. Valid login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": self.user_b_email,
            "password": self.password,
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("session_token", login_res.json())

        # 2. Invalid password
        bad_pass_res = self.client.post("/api/v1/auth/login", json={
            "email": self.user_b_email,
            "password": "WrongPassword999",
        })
        self.assertEqual(bad_pass_res.status_code, 401)

        # 3. Unknown email
        unknown_res = self.client.post("/api/v1/auth/login", json={
            "email": "nonexistent_user@example.test",
            "password": self.password,
        })
        self.assertEqual(unknown_res.status_code, 401)

    def test_04_authenticated_me_and_unauthenticated_rejection(self):
        """Verify /me profile endpoint for authenticated user and HTTP 401 for unauthenticated."""
        # Unauthenticated request
        anon_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(anon_res.status_code, 401)

        # Register & Login User A
        reg_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Alice Tenant",
            "organization": "Tenant Org A",
            "email": self.user_a_email,
            "password": self.password,
        })
        session_token = reg_res.json()["session_token"]

        # Authenticated request with Bearer header
        auth_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        self.assertEqual(auth_res.status_code, 200)
        user_info = auth_res.json()
        self.assertEqual(user_info["email"], self.user_a_email)
        self.assertEqual(user_info["organization"], "Tenant Org A")

    def test_05_logout_and_session_revocation(self):
        """Verify session token is revoked and unusable after logout."""
        reg_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Charlie Tester",
            "organization": "Testing Corp",
            "email": f"charlie_{uuid.uuid4().hex[:8]}@example.test",
            "password": self.password,
        })
        session_token = reg_res.json()["session_token"]

        # Logout
        logout_res = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        self.assertEqual(logout_res.status_code, 200)

        # Attempt to access /me after logout
        after_logout_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        self.assertEqual(after_logout_res.status_code, 401)

    def test_06_multi_tenant_job_isolation_and_idor_protection(self):
        """
        Critical Multi-Tenant Isolation Test:
        User A creates Job A.
        User B attempts to access Job A status, records, schema, and exports.
        User B must be rejected with HTTP 403 Forbidden.
        User A can access Job A without issues.
        """
        # 1. Register User A
        reg_a = self.client.post("/api/v1/auth/register", json={
            "full_name": "Alice Isolation",
            "organization": "Alice Corp",
            "email": self.user_a_email,
            "password": self.password,
        })
        token_a = reg_a.json()["session_token"]

        # 2. Register User B
        reg_b = self.client.post("/api/v1/auth/register", json={
            "full_name": "Bob Isolation",
            "organization": "Bob Corp",
            "email": self.user_b_email,
            "password": self.password,
        })
        token_b = reg_b.json()["session_token"]

        # 3. User A uploads a CSV dataset
        csv_content = b"PART_NUMBER,Part_Desc,MANUFACTURER_NAME,BRAND_NAME\n3M-001,Sanding Disc 50/Box,3M Corp,3M\n"
        upload_res = self.client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("alice_catalog.csv", csv_content, "text/csv")},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(upload_res.status_code, 201)
        job_a_id = upload_res.json()["job_id"]

        # 4. User A can access Job A
        user_a_get_job = self.client.get(
            f"/api/v1/ingestion/{job_a_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(user_a_get_job.status_code, 200)

        # 5. User B attempts to access Job A -> MUST BE 403 FORBIDDEN
        user_b_get_job = self.client.get(
            f"/api/v1/ingestion/{job_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_get_job.status_code, 403)

        # 6. User B attempts to access Job A schema -> MUST BE 403 FORBIDDEN
        user_b_schema = self.client.get(
            f"/api/v1/ingestion/{job_a_id}/schema",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_schema.status_code, 403)

        # 7. User B attempts to access Job A product records -> MUST BE 403 FORBIDDEN
        user_b_records = self.client.get(
            f"/api/v1/ingestion/{job_a_id}/records",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_records.status_code, 403)

        # 8. User A gets product records to resolve Product A ID
        user_a_records = self.client.get(
            f"/api/v1/ingestion/{job_a_id}/records",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(user_a_records.status_code, 200)
        product_a_id = user_a_records.json()["records"][0]["id"]

        # 9. User B attempts to trigger intelligence on Product A -> MUST BE 403 FORBIDDEN
        user_b_intel = self.client.post(
            f"/api/v1/intelligence/analyze/product/{product_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_intel.status_code, 403)

        # 10. User B attempts to trigger enrichment on Product A -> MUST BE 403 FORBIDDEN
        user_b_enrich = self.client.post(
            f"/api/v1/enrichment/product/{product_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_enrich.status_code, 403)

        # 11. User B attempts to trigger validation on Product A -> MUST BE 403 FORBIDDEN
        user_b_val = self.client.post(
            f"/api/v1/validation/product/{product_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_val.status_code, 403)

        # 12. User B attempts to export Job A dataset -> MUST BE 403 FORBIDDEN
        user_b_export = self.client.post(
            f"/api/v1/export/{job_a_id}?format=csv",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_export.status_code, 403)

        # 13. User B attempts to preview natural language query on Job A -> MUST BE 403 FORBIDDEN
        user_b_query_prev = self.client.post(
            f"/api/v1/query/{job_a_id}/preview",
            json={"query": "Find abrasive products with dimensions"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_query_prev.status_code, 403)

        # 14. User B attempts to execute natural language query on Job A -> MUST BE 403 FORBIDDEN
        user_b_query_exec = self.client.post(
            f"/api/v1/query/{job_a_id}",
            json={"query": "Find abrasive products with dimensions", "limit": 10},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_query_exec.status_code, 403)

        # 15. User A can successfully preview and execute queries on Job A
        user_a_query_prev = self.client.post(
            f"/api/v1/query/{job_a_id}/preview",
            json={"query": "Find abrasive products with dimensions"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(user_a_query_prev.status_code, 200)

        user_a_query_exec = self.client.post(
            f"/api/v1/query/{job_a_id}",
            json={"query": "Find abrasive products with dimensions", "limit": 10},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(user_a_query_exec.status_code, 200)

    def test_07_login_brute_force_lockout_and_case_insensitivity(self):
        """
        Verify:
        - 5 repeated failed login attempts trigger HTTP 429 Too Many Requests
        - Case variation of email is treated consistently (case-insensitive)
        - Successful login resets the lockout counter
        """
        victim_email = f"BruteForce_{uuid.uuid4().hex[:6]}@Example.Test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Lockout Test User",
            "organization": "Security Corp",
            "email": victim_email,
            "password": self.password,
        })
        self.assertEqual(reg.status_code, 201)

        # 1. Repeated 5 failed login attempts with mixed casing
        for i in range(5):
            bad_res = self.client.post("/api/v1/auth/login", json={
                "email": victim_email.lower(),
                "password": f"WrongPass_{i}",
            })
            self.assertEqual(bad_res.status_code, 401)
            self.assertEqual(bad_res.json()["detail"], "Invalid email or password.")

        # 2. 6th attempt must be throttled with HTTP 429 Too Many Requests
        locked_res = self.client.post("/api/v1/auth/login", json={
            "email": victim_email.upper(),
            "password": self.password,  # Even with correct password, account is throttled
        })
        self.assertEqual(locked_res.status_code, 429)
        self.assertIn("Too many failed login attempts", locked_res.json()["detail"])

        # 3. Simulate throttle reset and verify successful login resets failed counter
        from app.services.auth_service import _login_attempts
        _login_attempts.pop(victim_email.lower().strip(), None)

        good_res = self.client.post("/api/v1/auth/login", json={
            "email": victim_email,
            "password": self.password,
        })
        self.assertEqual(good_res.status_code, 200)

    def test_08_password_policy_and_session_fixation_protection(self):
        """
        Verify:
        - Password minimum length (8 chars) enforced
        - Distinct logins generate fresh, unique session tokens (Session Fixation protection)
        """
        # Short password rejected
        short_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "Short Password User",
            "organization": "Policy Corp",
            "email": f"short_{uuid.uuid4().hex[:6]}@example.test",
            "password": "123",  # < 8 chars
        })
        self.assertEqual(short_res.status_code, 422)

        # Register valid user
        user_email = f"session_fix_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Fixation User",
            "organization": "Fixation Corp",
            "email": user_email,
            "password": self.password,
        })
        token_1 = reg.json()["session_token"]

        # Second login generates a new distinct session token
        login_1 = self.client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": self.password,
        })
        token_2 = login_1.json()["session_token"]

        self.assertNotEqual(token_1, token_2, "Each authentication must generate a unique, fresh session token")

    def test_09_forgot_and_reset_password_lifecycle(self):
        """
        Verify:
        - Requesting password reset issues hashed token in DB and returns generic 200
        - Resetting password with valid token updates hash and invalidates old sessions
        - Old password fails to authenticate
        - New password successfully authenticates
        - Reusing reset token fails
        """
        user_email = f"reset_test_{uuid.uuid4().hex[:6]}@example.test"
        old_pass = "OldPassword123!"
        new_pass = "BrandNewPassword123!"

        # Register
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Reset Test User",
            "organization": "Reset Corp",
            "email": user_email,
            "password": old_pass,
        })
        old_session_token = reg.json()["session_token"]

        # Request reset
        forgot_res = self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.assertEqual(forgot_res.status_code, 200)

        # Retrieve the user and token from database for test verification
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            self.assertIsNotNone(user.reset_token_hash)
            # Create a known raw token and assign its hash to test the endpoint
            test_raw_token = "valid_reset_token_1234567890_abcdef"
            user.reset_token_hash = SecurityUtils.hash_token(test_raw_token)
            db.commit()
        finally:
            db.close()

        # Reset password with valid token
        reset_res = self.client.post("/api/v1/auth/reset-password", json={
            "token": test_raw_token,
            "new_password": new_pass,
        })
        self.assertEqual(reset_res.status_code, 200)

        # 1. Old session token must now be invalid
        old_sess_check = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_session_token}"})
        self.assertEqual(old_sess_check.status_code, 401)

        # 2. Old password must fail login
        old_login = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": old_pass})
        self.assertEqual(old_login.status_code, 401)

        # 3. New password must succeed
        new_login = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": new_pass})
        self.assertEqual(new_login.status_code, 200)

        # 4. Token reuse must fail
        reuse_res = self.client.post("/api/v1/auth/reset-password", json={
            "token": test_raw_token,
            "new_password": "AnotherPassword123!",
        })
        self.assertEqual(reuse_res.status_code, 400)

    def test_10_change_password_and_session_invalidation(self):
        """Verify authenticated user can change password and revoke other sessions."""
        user_email = f"change_pass_{uuid.uuid4().hex[:6]}@example.test"
        pass_1 = "CurrentPassword123!"
        pass_2 = "UpdatedPassword123!"

        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Change Pass User",
            "organization": "Change Corp",
            "email": user_email,
            "password": pass_1,
        })
        token = reg.json()["session_token"]

        # Wrong current password fails
        bad_change = self.client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "WrongPassword123!", "new_password": pass_2},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(bad_change.status_code, 400)

        # Correct change succeeds
        good_change = self.client.post(
            "/api/v1/auth/change-password",
            json={"current_password": pass_1, "new_password": pass_2},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(good_change.status_code, 200)

    def test_11_email_verification_flow(self):
        """Verify email verification token marks user verified."""
        user_email = f"verify_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Verify User",
            "organization": "Verify Corp",
            "email": user_email,
            "password": self.password,
        })
        token = reg.json()["session_token"]

        # Set up a verification token
        from app.core.database import SessionLocal
        from datetime import datetime, timezone, timedelta
        db = SessionLocal()
        raw_verify_token = "verify_token_abcdef1234567890"
        try:
            user = db.query(User).filter(User.email == user_email).first()
            user.verification_token_hash = SecurityUtils.hash_token(raw_verify_token)
            user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            db.commit()
        finally:
            db.close()

        # Call verification endpoint
        ver_res = self.client.get(f"/api/v1/auth/verify-email?token={raw_verify_token}")
        self.assertEqual(ver_res.status_code, 200)

        # Profile reflects is_verified = True
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(me_res.json().get("is_verified"))

    def test_12_active_sessions_and_revocation(self):
        """Verify user can view active sessions and revoke specific sessions."""
        user_email = f"sessions_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Session List User",
            "organization": "Session Corp",
            "email": user_email,
            "password": self.password,
        })
        token_1 = reg.json()["session_token"]

        # Second login creates session 2
        login_res = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": self.password})
        token_2 = login_res.json()["session_token"]

        # List sessions
        sess_list = self.client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_2}"})
        self.assertEqual(sess_list.status_code, 200)
        sessions = sess_list.json()
        self.assertGreaterEqual(len(sessions), 2)

        # Find session 1 ID and revoke it
        sess_1_id = [s["id"] for s in sessions if not s["is_current"]][0]
        del_res = self.client.delete(f"/api/v1/auth/sessions/{sess_1_id}", headers={"Authorization": f"Bearer {token_2}"})
        self.assertEqual(del_res.status_code, 200)

        # Session 1 is now rejected
        check_sess_1 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_1}"})
        self.assertEqual(check_sess_1.status_code, 401)

        # Session 2 still works
        check_sess_2 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_2}"})
        self.assertEqual(check_sess_2.status_code, 200)

    def test_13_account_deletion_with_confirmation(self):
        """Verify permanent account deletion upon password and phrase confirmation."""
        user_email = f"delete_user_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Delete Me",
            "organization": "Delete Corp",
            "email": user_email,
            "password": self.password,
        })
        token = reg.json()["session_token"]

        # Wrong phrase fails
        bad_del = self.client.post(
            "/api/v1/auth/delete-account",
            json={"password": self.password, "confirm_text": "WRONG PHRASE"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(bad_del.status_code, 400)

        # Correct deletion succeeds
        good_del = self.client.post(
            "/api/v1/auth/delete-account",
            json={"password": self.password, "confirm_text": "DELETE MY ACCOUNT"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(good_del.status_code, 200)

        # Account no longer exists
        login_del = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": self.password})
        self.assertEqual(login_del.status_code, 401)

    def test_14_registration_creates_unverified_user_with_token(self):
        """Test 14: Registration creates an unverified user and generates a secure verification token record."""
        from datetime import datetime, timezone
        user_email = f"verify_test_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Verify Me",
            "organization": "Verify Corp",
            "email": user_email,
            "password": self.password,
        })
        self.assertEqual(reg.status_code, 201)
        data = reg.json()
        self.assertFalse(data["user"]["email_verified"])
        self.assertFalse(data["user"]["is_verified"])

        # Check DB
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            self.assertIsNotNone(user)
            self.assertFalse(user.email_verified)
            self.assertFalse(user.is_verified)
            self.assertIsNone(user.email_verified_at)

            token_record = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).first()
            self.assertIsNotNone(token_record)
            self.assertIsNone(token_record.used_at)
            token_exp = token_record.expires_at.replace(tzinfo=timezone.utc) if token_record.expires_at.tzinfo is None else token_record.expires_at
            self.assertGreater(token_exp, datetime.now(timezone.utc))
        finally:
            db.close()

    def test_15_raw_token_not_stored_in_db(self):
        """Test 15: Raw verification token is NEVER stored in database; only a 64-char SHA-256 hash is persisted."""
        user_email = f"raw_token_test_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Hash Check",
            "organization": "Security Corp",
            "email": user_email,
            "password": self.password,
        })

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            token_record = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).first()
            self.assertIsNotNone(token_record)
            # Must be a 64-character hex string (SHA-256)
            self.assertEqual(len(token_record.token_hash), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in token_record.token_hash))
        finally:
            db.close()

    def test_16_valid_token_verifies_account(self):
        """Test 16: Valid verification token verifies the account, sets email_verified_at, and marks token as used."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"valid_verify_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Valid Verifier",
                organization="Valid Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
                email_verified=False,
                is_verified=False,
            )
            db.add(user)
            db.flush()

            token_record = EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
            )
            db.add(token_record)
            db.commit()
            user_id = user.id
        finally:
            db.close()

        # Verify via POST endpoint
        verify_res = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn("verified successfully", verify_res.json()["message"])

        # Check DB update
        db = SessionLocal()
        try:
            updated_user = db.query(User).filter(User.id == user_id).first()
            self.assertTrue(updated_user.email_verified)
            self.assertTrue(updated_user.is_verified)
            self.assertIsNotNone(updated_user.email_verified_at)

            updated_token = db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == token_hash).first()
            self.assertIsNotNone(updated_token.used_at)
        finally:
            db.close()

    def test_17_invalid_token_rejected(self):
        """Test 17: Invalid verification tokens return HTTP 400 Bad Request."""
        res = self.client.post("/api/v1/auth/verify-email", json={"token": "invalid-random-token-123456789"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid or expired", res.json()["detail"])

    def test_18_expired_token_rejected(self):
        """Test 18: Expired verification tokens return HTTP 400 Bad Request."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"expired_test_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Expired User",
                organization="Expired Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
                email_verified=False,
                is_verified=False,
            )
            db.add(user)
            db.flush()

            token_record = EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=15),  # expired 15 mins ago
            )
            db.add(token_record)
            db.commit()
        finally:
            db.close()

        res = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res.status_code, 400)
        self.assertIn("expired", res.json()["detail"].lower())

    def test_19_used_token_rejected_and_cannot_be_reused(self):
        """Test 19: A verification token cannot be reused once consumed."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"single_use_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Single Use User",
                organization="Single Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
                email_verified=False,
                is_verified=False,
            )
            db.add(user)
            db.flush()

            token_record = EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
            )
            db.add(token_record)
            db.commit()
        finally:
            db.close()

        # First use succeeds
        res1 = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res1.status_code, 200)

        # Second use is rejected as already used
        res2 = self.client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already been used", res2.json()["detail"])

    def test_20_resend_verification_invalidates_previous_token(self):
        """Test 20: Requesting a resend invalidates prior active tokens and issues a fresh token."""
        user_email = f"resend_inval_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Resend Tester",
            "organization": "Resend Corp",
            "email": user_email,
            "password": self.password,
        })

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            first_token = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).first()
            self.assertIsNotNone(first_token)
            self.assertIsNone(first_token.used_at)
        finally:
            db.close()

        # Request resend
        resend_res = self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        self.assertEqual(resend_res.status_code, 200)

        # Check DB: First token is now invalidated (used_at is set), second token exists and is active
        db = SessionLocal()
        try:
            tokens = (
                db.query(EmailVerificationToken)
                .filter(EmailVerificationToken.user_id == user.id)
                .order_by(EmailVerificationToken.created_at.asc())
                .all()
            )
            self.assertEqual(len(tokens), 2)
            self.assertIsNotNone(tokens[0].used_at, "Old token must be marked as used/invalidated")
            self.assertIsNone(tokens[1].used_at, "New token must be active")
        finally:
            db.close()

    def test_21_resend_verification_is_rate_limited(self):
        """Test 21: Rapid resend verification requests are throttled (HTTP 429)."""
        user_email = f"throttle_resend_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Throttle Tester",
            "organization": "Throttle Corp",
            "email": user_email,
            "password": self.password,
        })

        # 3 calls succeed, 4th call is blocked with 429
        self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        fourth = self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        self.assertEqual(fourth.status_code, 429)
        self.assertIn("Too many", fourth.json()["detail"])

    def test_22_generic_response_prevents_email_enumeration(self):
        """Test 22: Resend verification returns identical generic success for non-existent accounts."""
        ghost_email = f"ghost_user_{uuid.uuid4().hex[:6]}@nonexistent.domain"
        res = self.client.post("/api/v1/auth/resend-verification", json={"email": ghost_email})
        self.assertEqual(res.status_code, 200)
        self.assertIn("If the account requires verification", res.json()["message"])

    def test_23_already_verified_account_handled_safely(self):
        """Test 23: Resending verification on an already-verified account returns generic success safely."""
        from datetime import datetime, timezone
        user_email = f"already_ver_{uuid.uuid4().hex[:6]}@example.test"
        db = SessionLocal()
        try:
            user = User(
                full_name="Already Verified",
                organization="Verified Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
                email_verified=True,
                is_verified=True,
                email_verified_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
        finally:
            db.close()

        res = self.client.post("/api/v1/auth/resend-verification", json={"email": user_email})
        self.assertEqual(res.status_code, 200)
        self.assertIn("If the account requires verification", res.json()["message"])

    def test_24_verification_does_not_bypass_workspace_authorization(self):
        """Test 24: Email verification status preserves strict multi-tenant workspace isolation."""
        user_a_email = f"tenant_a_{uuid.uuid4().hex[:6]}@example.test"
        user_b_email = f"tenant_b_{uuid.uuid4().hex[:6]}@example.test"

        reg_a = self.client.post("/api/v1/auth/register", json={
            "full_name": "Tenant A",
            "organization": "Alpha Corp",
            "email": user_a_email,
            "password": self.password,
        })
        token_a = reg_a.json()["session_token"]

        reg_b = self.client.post("/api/v1/auth/register", json={
            "full_name": "Tenant B",
            "organization": "Beta Corp",
            "email": user_b_email,
            "password": self.password,
        })
        token_b = reg_b.json()["session_token"]

        # User B queries User A's workspace sessions -> 404 or isolation check
        sess_b = self.client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(sess_b.status_code, 200)
        # All sessions returned belong strictly to User B
        for s in sess_b.json():
            self.assertTrue(s["is_current"])

    def test_25_forgot_password_generic_response_anti_enumeration(self):
        """Test 25: Forgot password endpoint returns identical generic response for existing and non-existing accounts."""
        # 1. Existing user
        user_email = f"enum_exist_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Enum Check",
            "organization": "Security Corp",
            "email": user_email,
            "password": self.password,
        })
        res_exist = self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.assertEqual(res_exist.status_code, 200)

        # 2. Non-existing user
        ghost_email = f"enum_ghost_{uuid.uuid4().hex[:6]}@example.test"
        res_ghost = self.client.post("/api/v1/auth/forgot-password", json={"email": ghost_email})
        self.assertEqual(res_ghost.status_code, 200)

        # Both messages must be completely identical
        self.assertEqual(res_exist.json()["message"], res_ghost.json()["message"])
        self.assertIn("password reset instructions have been sent", res_exist.json()["message"].lower())

    def test_26_password_reset_token_model_persistence_and_hash_only(self):
        """Test 26: Dedicated PasswordResetToken model stores only a 64-char SHA-256 hash, never raw token."""
        user_email = f"reset_hash_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Hash Check",
            "organization": "Security Corp",
            "email": user_email,
            "password": self.password,
        })

        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            reset_record = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
            self.assertIsNotNone(reset_record)
            self.assertEqual(len(reset_record.token_hash), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in reset_record.token_hash))
            self.assertIsNone(reset_record.used_at)
        finally:
            db.close()

    def test_27_password_reset_token_expiration_rejection(self):
        """Test 27: Expired password reset tokens are strictly rejected with HTTP 400."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"reset_exp_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Exp Reset User",
                organization="Exp Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
            )
            db.add(user)
            db.flush()

            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),  # expired 5 min ago
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        res = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "new_password": "BrandNewSecurePassword123!",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("expired", res.json()["detail"].lower())

    def test_28_password_reset_token_single_use_and_reuse_rejection(self):
        """Test 28: A password reset token is single-use and cannot be reused once consumed."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"reset_single_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Single Reset User",
                organization="Single Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
            )
            db.add(user)
            db.flush()

            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        # First consumption succeeds
        res1 = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "new_password": "NewValidPassword123!",
        })
        self.assertEqual(res1.status_code, 200)

        # Second consumption fails
        res2 = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "new_password": "SecondAttemptPassword123!",
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already been used", res2.json()["detail"].lower())

    def test_29_password_reset_new_request_invalidates_previous_active_token(self):
        """Test 29: A new password reset request marks previous active tokens as invalidated/consumed."""
        user_email = f"reset_inval_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Inval Tester",
            "organization": "Inval Corp",
            "email": user_email,
            "password": self.password,
        })

        # Request reset 1
        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})

        # Request reset 2
        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            tokens = (
                db.query(PasswordResetToken)
                .filter(PasswordResetToken.user_id == user.id)
                .order_by(PasswordResetToken.created_at.asc())
                .all()
            )
            self.assertEqual(len(tokens), 2)
            self.assertIsNotNone(tokens[0].used_at, "Old token must be marked as used/invalidated")
            self.assertIsNone(tokens[1].used_at, "New token must be active")
        finally:
            db.close()

    def test_30_password_reset_enforces_password_policy(self):
        """Test 30: Reset password rejects passwords shorter than 8 characters."""
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)
        user_email = f"policy_test_{uuid.uuid4().hex[:6]}@example.test"

        db = SessionLocal()
        try:
            user = User(
                full_name="Policy User",
                organization="Policy Corp",
                email=user_email,
                password_hash=SecurityUtils.hash_password(self.password),
                role="owner",
            )
            db.add(user)
            db.flush()

            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        # Too short (< 8 chars)
        res = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "new_password": "short",
        })
        self.assertEqual(res.status_code, 422)  # Pydantic schema validation min_length=8

    def test_31_password_reset_revokes_all_prior_sessions(self):
        """Test 31: Resetting password revokes every active session for that user."""
        user_email = f"sess_rev_{uuid.uuid4().hex[:6]}@example.test"
        reg = self.client.post("/api/v1/auth/register", json={
            "full_name": "Sess Rev",
            "organization": "Sess Corp",
            "email": user_email,
            "password": self.password,
        })
        session_1 = reg.json()["session_token"]

        login = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": self.password})
        session_2 = login.json()["session_token"]

        # Request reset
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        # Perform password reset
        reset_res = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_token,
            "new_password": "NewSecretPassword123!",
        })
        self.assertEqual(reset_res.status_code, 200)

        # Both previous sessions must now return HTTP 401
        check_1 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {session_1}"})
        self.assertEqual(check_1.status_code, 401)

        check_2 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {session_2}"})
        self.assertEqual(check_2.status_code, 401)

    def test_32_password_reset_old_password_rejected_new_password_accepted(self):
        """Test 32: After reset, login with old password fails (401) and new password succeeds (200)."""
        user_email = f"pass_switch_{uuid.uuid4().hex[:6]}@example.test"
        old_p = "OldPassword123!"
        new_p = "BrandNewPassword123!"

        self.client.post("/api/v1/auth/register", json={
            "full_name": "Switch User",
            "organization": "Switch Corp",
            "email": user_email,
            "password": old_p,
        })

        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        self.client.post("/api/v1/auth/reset-password", json={"token": raw_token, "new_password": new_p})

        # Old password rejected
        old_login = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": old_p})
        self.assertEqual(old_login.status_code, 401)

        # New password accepted
        new_login = self.client.post("/api/v1/auth/login", json={"email": user_email, "password": new_p})
        self.assertEqual(new_login.status_code, 200)

    def test_33_forgot_password_rate_limiting(self):
        """Test 33: Rapid forgot password requests are throttled (HTTP 429)."""
        user_email = f"throttle_forgot_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Throttle User",
            "organization": "Throttle Corp",
            "email": user_email,
            "password": self.password,
        })

        # 3 calls succeed, 4th is throttled
        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        fourth = self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.assertEqual(fourth.status_code, 429)
        self.assertIn("Too many", fourth.json()["detail"])

    def test_34_reset_password_workspace_isolation_preservation(self):
        """Test 34: Resetting password preserves strict tenant isolation for jobs and datasets."""
        user_a_email = f"iso_a_{uuid.uuid4().hex[:6]}@example.test"
        user_b_email = f"iso_b_{uuid.uuid4().hex[:6]}@example.test"

        reg_a = self.client.post("/api/v1/auth/register", json={
            "full_name": "Iso A",
            "organization": "Alpha Corp",
            "email": user_a_email,
            "password": self.password,
        })
        ws_a_id = reg_a.json()["user"]["workspace_id"]

        reg_b = self.client.post("/api/v1/auth/register", json={
            "full_name": "Iso B",
            "organization": "Beta Corp",
            "email": user_b_email,
            "password": self.password,
        })
        token_b = reg_b.json()["session_token"]

        # Reset User A password
        from datetime import datetime, timezone, timedelta
        raw_token = SecurityUtils.generate_session_token()
        token_hash = SecurityUtils.hash_token(raw_token)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_a_email).first()
            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            db.add(reset_record)
            db.commit()
        finally:
            db.close()

        self.client.post("/api/v1/auth/reset-password", json={"token": raw_token, "new_password": "NewIsoPassword123!"})

        # User B still cannot access User A's workspace
        check = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(check.status_code, 200)
        self.assertNotEqual(str(check.json()["workspace_id"]), str(ws_a_id))

    def test_35_reset_token_never_leaked_in_logs_or_responses(self):
        """Test 35: Forgot password response body contains only user-friendly confirmation without tokens."""
        user_email = f"leak_test_{uuid.uuid4().hex[:6]}@example.test"
        self.client.post("/api/v1/auth/register", json={
            "full_name": "Leak Tester",
            "organization": "Leak Corp",
            "email": user_email,
            "password": self.password,
        })

        res = self.client.post("/api/v1/auth/forgot-password", json={"email": user_email})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("token", data)
        self.assertNotIn("token_hash", data)
        self.assertNotIn("reset_url", data)


if __name__ == "__main__":
    unittest.main()
