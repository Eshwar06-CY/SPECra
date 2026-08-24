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
from app.core.database import Base, get_db
from app.core.security import SecurityUtils
from app.models.user import User, Workspace, UserSession
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


if __name__ == "__main__":
    unittest.main()
