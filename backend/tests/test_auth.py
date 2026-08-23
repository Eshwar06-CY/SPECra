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


if __name__ == "__main__":
    unittest.main()
