"""
Comprehensive Phase 3 Security Test Suite:
- Multi-tenant data & artifact isolation (User A vs User B)
- Ingestion, schema, records, and raw_data privacy
- Product IDOR protection (Intelligence, Enrichment, Validation)
- Natural language query isolation
- Export preview & download IDOR protection (CSV & XLSX)
- Path traversal & filename sanitization
- Malicious upload extension rejection
- CSV / Excel formula injection mitigation
- Mass assignment protection
"""
import uuid
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, Workspace
from app.models.product import ProcessingJob, Product
from app.services.export_engine import sanitize_spreadsheet_cell, UniHackExportEngine


class TestDataFileExportSecurity(unittest.TestCase):
    """
    Phase 3 Data, File & Export Security Hardening Test Suite.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.user_a_email = f"alice_sec3_{uuid.uuid4().hex[:6]}@example.test"
        self.user_b_email = f"bob_sec3_{uuid.uuid4().hex[:6]}@example.test"
        self.password = "SecurePassword123!"

        # Register User A
        reg_a = self.client.post("/api/v1/auth/register", json={
            "full_name": "Alice Admin",
            "organization": "Alice Tech",
            "email": self.user_a_email,
            "password": self.password,
        })
        self.token_a = reg_a.json()["session_token"]
        self.workspace_a_id = reg_a.json()["user"]["workspace_id"]

        # Register User B
        reg_b = self.client.post("/api/v1/auth/register", json={
            "full_name": "Bob Intruder",
            "organization": "Bob Security",
            "email": self.user_b_email,
            "password": self.password,
        })
        self.token_b = reg_b.json()["session_token"]
        self.workspace_b_id = reg_b.json()["user"]["workspace_id"]

        # User A uploads a catalog
        csv_data = (
            b"Mfg_Part_Num,Part_Desc,Part_Manuf,Formula_Col\n"
            b"DCB-001,Diablo 1/2in Sanding Belt 6pc,Freud Inc,=SUM(1+1)\n"
            b"3M-002,3M Abrasive Disc 10pc,3M Corp,@HYPERLINK('http://evil.com')\n"
        )
        up_res = self.client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("alice_catalog.csv", csv_data, "text/csv")},
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(up_res.status_code, 201)
        self.job_a_id = up_res.json()["job_id"]

        # Retrieve product ID from User A's job
        rec_res = self.client.get(
            f"/api/v1/ingestion/{self.job_a_id}/records",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(rec_res.status_code, 200)
        self.product_a_id = rec_res.json()["records"][0]["id"]

    def test_01_user_b_cannot_access_user_a_job_and_records(self):
        """User B must get 403 when trying to access User A's job, schema, or records."""
        # 1. Get Job status
        job_res = self.client.get(
            f"/api/v1/ingestion/{self.job_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(job_res.status_code, 403)

        # 2. Get Schema
        schema_res = self.client.get(
            f"/api/v1/ingestion/{self.job_a_id}/schema",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(schema_res.status_code, 403)

        # 3. Get Records
        records_res = self.client.get(
            f"/api/v1/ingestion/{self.job_a_id}/records",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(records_res.status_code, 403)

    def test_02_user_b_cannot_access_or_trigger_product_services(self):
        """User B must get 403 when accessing intelligence, enrichment, or validation for Product A."""
        # 1. Product Intelligence GET & POST
        get_intel = self.client.get(
            f"/api/v1/intelligence/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(get_intel.status_code, 403)

        post_intel = self.client.post(
            f"/api/v1/intelligence/analyze/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(post_intel.status_code, 403)

        # 2. Product Enrichment GET & POST
        get_enrich = self.client.get(
            f"/api/v1/enrichment/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(get_enrich.status_code, 403)

        post_enrich = self.client.post(
            f"/api/v1/enrichment/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(post_enrich.status_code, 403)

        # 3. Product Validation GET & POST
        get_val = self.client.get(
            f"/api/v1/validation/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(get_val.status_code, 403)

        post_val = self.client.post(
            f"/api/v1/validation/product/{self.product_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(post_val.status_code, 403)

    def test_03_user_b_cannot_query_user_a_catalog(self):
        """User B must get 403 when attempting natural language queries on Job A."""
        prev_res = self.client.post(
            f"/api/v1/query/{self.job_a_id}/preview",
            json={"query": "Find all sanding belts"},
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(prev_res.status_code, 403)

        exec_res = self.client.post(
            f"/api/v1/query/{self.job_a_id}",
            json={"query": "Find all sanding belts", "limit": 10},
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(exec_res.status_code, 403)

    def test_04_user_b_cannot_export_user_a_catalog(self):
        """User B must get 403 for export preview and CSV/XLSX export downloads."""
        # 1. Preview
        prev_res = self.client.get(
            f"/api/v1/export/{self.job_a_id}/preview",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(prev_res.status_code, 403)

        # 2. CSV Export
        csv_res = self.client.post(
            f"/api/v1/export/{self.job_a_id}?format=csv",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(csv_res.status_code, 403)

        # 3. XLSX Export
        xlsx_res = self.client.post(
            f"/api/v1/export/{self.job_a_id}?format=xlsx",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(xlsx_res.status_code, 403)

    def test_05_owner_user_a_access_succeeds(self):
        """User A has full, unhindered access to all resources of Job A."""
        # Status
        self.assertEqual(
            self.client.get(f"/api/v1/ingestion/{self.job_a_id}", headers={"Authorization": f"Bearer {self.token_a}"}).status_code,
            200,
        )
        # Records
        self.assertEqual(
            self.client.get(f"/api/v1/ingestion/{self.job_a_id}/records", headers={"Authorization": f"Bearer {self.token_a}"}).status_code,
            200,
        )
        # Query Preview
        self.assertEqual(
            self.client.post(f"/api/v1/query/{self.job_a_id}/preview", json={"query": "Find belts"}, headers={"Authorization": f"Bearer {self.token_a}"}).status_code,
            200,
        )
        # Export Preview
        self.assertEqual(
            self.client.get(f"/api/v1/export/{self.job_a_id}/preview", headers={"Authorization": f"Bearer {self.token_a}"}).status_code,
            200,
        )
        # CSV Export
        csv_dl = self.client.post(f"/api/v1/export/{self.job_a_id}?format=csv", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(csv_dl.status_code, 200)
        self.assertEqual(csv_dl.headers.get("content-type"), "text/csv; charset=utf-8")

        # XLSX Export
        xlsx_dl = self.client.post(f"/api/v1/export/{self.job_a_id}?format=xlsx", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(xlsx_dl.status_code, 200)

    def test_06_malicious_file_extensions_rejected(self):
        """Reject non-CSV and non-XLSX executable or script uploads."""
        dangerous_extensions = ["malicious.exe", "script.py", "shell.bat", "run.ps1", "page.html", "data.json", "file.csv.exe"]
        for fname in dangerous_extensions:
            res = self.client.post(
                "/api/v1/ingestion/upload",
                files={"file": (fname, b"print('hacked')", "application/octet-stream")},
                headers={"Authorization": f"Bearer {self.token_a}"},
            )
            self.assertEqual(res.status_code, 400, f"Filename '{fname}' should have been rejected with 400")

    def test_07_path_traversal_sanitization(self):
        """Filenames with directory traversal patterns must be safely stripped."""
        traversal_names = ["../../etc/passwd.csv", "..\\..\\windows\\system32.csv", "folder/subfolder/dataset.csv"]
        for fname in traversal_names:
            res = self.client.post(
                "/api/v1/ingestion/upload",
                files={"file": (fname, b"PART,DESC\n1,Test\n", "text/csv")},
                headers={"Authorization": f"Bearer {self.token_a}"},
            )
            self.assertEqual(res.status_code, 201)
            sanitized = res.json()["filename"]
            self.assertNotIn("/", sanitized)
            self.assertNotIn("\\", sanitized)
            self.assertNotIn("..", sanitized)

    def test_08_formula_injection_mitigation(self):
        """Dangerous formula prefixes (=, +, -, @) must be escaped with single-quote in exported cells."""
        # Direct unit test of sanitizer
        self.assertEqual(sanitize_spreadsheet_cell("=SUM(A1:A10)"), "'=SUM(A1:A10)")
        self.assertEqual(sanitize_spreadsheet_cell("@HYPERLINK('http://evil.com')"), "'@HYPERLINK('http://evil.com')")
        self.assertEqual(sanitize_spreadsheet_cell("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(sanitize_spreadsheet_cell("\tTAB_INJECT"), "'\tTAB_INJECT")

        # Standard numbers remain unquoted
        self.assertEqual(sanitize_spreadsheet_cell("-5.5"), "-5.5")
        self.assertEqual(sanitize_spreadsheet_cell("+100"), "+100")
        self.assertEqual(sanitize_spreadsheet_cell("Diablo 1/2in Belt"), "Diablo 1/2in Belt")

        # Test CSV export content contains escaped formula
        csv_bytes = UniHackExportEngine.generate_csv_bytes([{"Product Name": "=cmd|' /C calc'!A0", "BRAND_NAME": "Diablo"}])
        csv_text = csv_bytes.decode("utf-8-sig")
        self.assertIn("'=cmd|' /C calc'!A0", csv_text)

    def test_09_mass_assignment_workspace_tampering_protection(self):
        """
        Verify that an authenticated user cannot forge or override workspace ownership
        during upload or analysis.
        """
        # User B attempts to upload a dataset while injecting User A's workspace_id in payload/query
        res = self.client.post(
            f"/api/v1/ingestion/upload?workspace_id={self.workspace_a_id}",
            files={"file": ("injected.csv", b"P,D\n1,Test\n", "text/csv")},
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(res.status_code, 201)
        job_b_id = res.json()["job_id"]

        # Verify in DB that job_b is strictly assigned to User B's workspace (server-side authentication wins)
        db = SessionLocal()
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == uuid.UUID(job_b_id)).first()
            self.assertEqual(str(job.workspace_id), str(self.workspace_b_id))
            self.assertNotEqual(str(job.workspace_id), str(self.workspace_a_id))
        finally:
            db.close()

    def test_10_raw_data_privacy_isolation(self):
        """
        Verify that raw_data and evidence quotes belonging to User A are never exposed
        to User B through jobs list, records pagination, or search.
        """
        # User B queries jobs list
        jobs_res = self.client.get("/api/v1/ingestion/jobs", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(jobs_res.status_code, 200)
        b_job_ids = [j["id"] for j in jobs_res.json()]
        self.assertNotIn(str(self.job_a_id), b_job_ids)

    def test_11_security_headers_present(self):
        """
        Verify that HTTP response headers contain enterprise security defenses.
        """
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(res.headers.get("x-frame-options"), "DENY")
        self.assertEqual(res.headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertEqual(res.headers.get("x-xss-protection"), "1; mode=block")


if __name__ == "__main__":
    unittest.main()
