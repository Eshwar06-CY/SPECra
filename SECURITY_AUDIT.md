# SPECra — Production Security Architecture & Audit Report

> **Target Application**: SPECra (Project DEADLOCK)  
> **Backend Architecture**: FastAPI, SQLAlchemy, PostgreSQL, Google Gemini AI (`gemini-3.7-flash`)  
> **Frontend Architecture**: React 19, TypeScript, Vite, TailwindCSS  
> **Date**: August 24, 2026  
> **Auditor**: Antigravity Security Agent  
> **Test Status**: **95 / 95 Backend Tests Passing (100% OK)** | **Frontend Build: Clean (0 Errors)**

---

## 1. Authentication

| Mechanism | Implementation Details | Classification |
| :--- | :--- | :--- |
| **Password Storage** | PBKDF2-HMAC-SHA256 with 100,000 iterations and a unique 16-byte cryptographically secure random salt per user. Plaintext passwords and reversible hashes are never stored or logged. | `IMPLEMENTED` |
| **Brute-Force Lockout** | In-memory failed attempt tracking (`_login_attempts`) in `AuthService`. Accounts are locked out for 300 seconds after 5 consecutive failed login attempts, returning `HTTP 429 Too Many Requests`. Successful logins immediately reset the failed counter. | `IMPLEMENTED` |
| **Credential Verification** | Constant-time `hmac.compare_digest` prevents timing attacks on password verification and token checks. | `IMPLEMENTED` |
| **User Enumeration Defense** | Constant-time uniform error response (`"Invalid email or password."`) on `/auth/login` and generic 200 responses on `/auth/forgot-password`. Case-insensitive email normalization is applied prior to lookups. | `IMPLEMENTED` |
| **Password Policy** | Strict minimum 8-character length enforced at registration, password reset, and profile change schemas. | `IMPLEMENTED` |
| **Distributed Rate Limiter** | Redis/Memcached backing for multi-server cluster environments. | `RECOMMENDED` |

---

## 2. Authorization & Insecure Direct Object Reference (IDOR) Protection

All backend endpoints enforce multi-tenant workspace ownership verification. A valid UUID is **never** sufficient to access another tenant's resources.

### Final Authorization & IDOR Matrix

| Endpoint | Method | Resource | Owner Access | Cross-Tenant Access | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/register` | `POST` | User/Workspace | Allowed | N/A (Public) | `IMPLEMENTED` |
| `/api/v1/auth/login` | `POST` | Session | Allowed | N/A (Public) | `IMPLEMENTED` |
| `/api/v1/auth/me` | `GET` | User Profile | Allowed (Self) | Blocked (`401 Unauthorized`) | `IMPLEMENTED` |
| `/api/v1/auth/logout` | `POST` | Session | Allowed (Self) | Blocked (`401 Unauthorized`) | `IMPLEMENTED` |
| `/api/v1/auth/forgot-password` | `POST` | Reset Token | Allowed (Self) | Generic 200 (No Enumeration) | `IMPLEMENTED` |
| `/api/v1/auth/reset-password` | `POST` | Password | Allowed (Token) | Blocked (`400 Bad Request`) | `IMPLEMENTED` |
| `/api/v1/auth/change-password` | `POST` | Password | Allowed (Self) | Blocked (`401 Unauthorized`) | `IMPLEMENTED` |
| `/api/v1/auth/verify-email` | `GET` | Email Token | Allowed (Token) | Blocked (`400 Bad Request`) | `IMPLEMENTED` |
| `/api/v1/auth/sessions` | `GET` | Active Sessions | Allowed (Self) | Blocked (`401 Unauthorized`) | `IMPLEMENTED` |
| `/api/v1/auth/sessions/{id}` | `DELETE` | Active Session | Allowed (Self) | Blocked (`403/404`) | `IMPLEMENTED` |
| `/api/v1/auth/delete-account` | `POST` | Account/Tenant | Allowed (Self) | Blocked (`401/403`) | `IMPLEMENTED` |
| `/api/v1/ingestion/upload` | `POST` | ProcessingJob | Allowed (Bound) | Server assigns caller workspace | `IMPLEMENTED` |
| `/api/v1/ingestion/jobs` | `GET` | Job Listing | Allowed (Tenant) | Filtered strictly to workspace | `IMPLEMENTED` |
| `/api/v1/ingestion/{job_id}` | `GET` | ProcessingJob | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/ingestion/{job_id}/schema` | `GET` | Schema Metadata | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/ingestion/{job_id}/records` | `GET` | Raw Records | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/intelligence/analyze/{job_id}` | `POST` | AI Execution | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/intelligence/analyze/product/{id}` | `POST` | AI Execution | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/intelligence/product/{id}` | `GET` | Product Intelligence | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/enrichment/product/{id}` | `GET/POST` | Enrichment Rules | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/validation/product/{id}` | `GET/POST` | Validation Audit | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/query/{job_id}/preview` | `POST` | Query Preview | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/query/{job_id}` | `POST` | Natural Query | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/export/{job_id}/preview` | `GET` | Export Preview | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |
| `/api/v1/export/{job_id}` | `POST` | CSV/XLSX Export | Allowed | Blocked (`403 Forbidden`) | `IMPLEMENTED` |

---

## 3. Multi-Tenant Isolation Model

The relational schema cleanly models tenant boundaries with cascading referential integrity:

```
User (id, email, password_hash, is_active, is_verified)
  └── 1:1 ──► Workspace (id, name, owner_id)
                └── 1:N ──► ProcessingJob (id, workspace_id, filename, status)
                              └── 1:N ──► Product (id, job_id, external_product_id, product_name, raw_data)
                                            ├── 1:N ──► ProductAttribute (product_id, attribute_name, value)
                                            ├── 1:N ──► FeatureHighlight (product_id, feature_text)
                                            ├── 1:N ──► Evidence (product_id, field_name, source_text)
                                            ├── 1:N ──► ProductEnrichment (product_id, field_name, value)
                                            └── 1:N ──► ValidationResult (product_id, rule_code, status)
```

- **Derived Ownership**: All sub-entities (`Product`, `ProductAttribute`, `Evidence`, `ProductEnrichment`, `ValidationResult`) link back to `job_id`. `ProcessingJob.workspace_id` acts as the authoritative boundary for multi-tenant isolation.
- **Mass Assignment Defense**: Server-side session authentication always assigns tenant ownership. Query parameters or request body fields attempting to inject a foreign `workspace_id` are strictly overridden by `auth[1].id`.

---

## 4. Data Protection & Raw Data Privacy

- **Catalog Isolation**: Raw catalog records (`raw_data`), OCR text, and evidence quotes are bound to `job_id` and are only queried with explicit workspace filters.
- **Minimal Response Sanitization**: API responses sanitize internal system metadata and strip password hashes, secret tokens, and cross-workspace references.
- **Database Level Filtering**: Pagination, filtering, and searches apply tenant isolation at the SQL query construction layer rather than in application memory.

---

## 5. File Upload & Storage Security

- **Extension Whitelisting**: Strict verification in `app/utils/file_parser.py` allowing only `.csv` and `.xlsx`. Executables (`.exe`, `.bat`, `.ps1`), scripts (`.py`, `.js`), web files (`.html`), and double-extension exploits (`file.csv.exe`) are rejected with `HTTP 400 Bad Request`.
- **Path Traversal Protection**: Directory prefixes (`../../`, `..\..\`) are stripped via `os.path.basename()` and regex sanitized (`re.sub(r"[^a-zA-Z0-9._-]", "_")`).
- **UUID-Partitioned Storage**: Files are saved with random UUID hex prefixes (`{uuid.uuid4().hex[:8]}_{filename}`) preventing overwrite collisions or directory snooping.
- **Upload Size Cap**: Maximum upload stream bounded to `50MB` (`MAX_UPLOAD_SIZE_MB`).

---

## 6. Export Security & Formula Injection Mitigation

- **Export Authorization**: `/api/v1/export/{job_id}` (CSV/XLSX) and `/api/v1/export/{job_id}/preview` enforce `job.workspace_id == auth[1].id` prior to generating or serving any data.
- **Direct Download Streaming**: Export files are generated in-memory or streamed directly via `Response(content=file_bytes)` with dynamic `Content-Disposition` headers, preventing unauthorized direct filesystem downloads.
- **Spreadsheet Formula Injection Mitigation**: Any cell starting with formula execution triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) is automatically sanitized by prepending a single quote (`'`) in `sanitize_spreadsheet_cell()`. Pure numeric values (e.g. `-5.5`, `+12`) remain unaltered.

---

## 7. AI Provider Security & Boundary

- **Server-Side API Key**: `GEMINI_API_KEY` is loaded exclusively on the backend via environment variables. It is never transmitted to the frontend, returned in API payloads, or written to application log files.
- **Prompt Isolation**: AI analysis prompts only include records from the validated caller's `job_id`. Unrelated workspace catalogs are never injected into context prompts.
- **Evidence-Grounded Extraction**: The Gemini pipeline uses strictly typed schema output parsing, verifying extracted values against source raw records to prevent hallucinations.

---

## 8. Session & Cookie Security

- **Dual-Mode Resolution**: Supports `HttpOnly` cookie extraction (`specra_session`) and `Authorization: Bearer <token>` headers for maximum client flexibility.
- **Session Revocation**: `POST /auth/logout` and `DELETE /auth/sessions/{id}` explicitly set `is_revoked = True` in the database, invalidating the session immediately.
- **Session Invalidation on Password Reset**: When a password is reset via `/auth/reset-password`, all existing active sessions for that user are revoked in the database.
- **Environment-Toggled Cookie Flags**:
  - Development: `HttpOnly=True`, `SameSite=Lax`, `Secure=False` (enables seamless localhost HTTP operation).
  - Production: `HttpOnly=True`, `SameSite=Lax`, `Secure=True` (configured via `COOKIE_SECURE=true`).

---

## 9. CORS Policy

- **Explicit Whitelisting**: `CORS_ORIGINS` strictly specifies permitted development endpoints (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`).
- **No Wildcard with Credentials**: The wildcard `"*"` has been removed from all configuration files to ensure secure operation with `allow_credentials=True`.

---

## 10. HTTP Security Headers

Injected via FastAPI HTTP middleware on all responses:
- `X-Content-Type-Options: nosniff` (prevents MIME-sniffing)
- `X-Frame-Options: DENY` (prevents clickjacking attacks)
- `Referrer-Policy: strict-origin-when-cross-origin` (prevents cross-origin referrer leakage)
- `X-XSS-Protection: 1; mode=block` (legacy XSS filtering defense)

---

## 11. Secrets Management

- **Repository Hygiene**:
  - `backend/.env` is listed in `.gitignore` and excluded from source control.
  - `backend/.env.example` contains only safe dummy placeholders.
  - `frontend/.env` contains only `VITE_API_BASE_URL=http://127.0.0.1:8001` (no private API keys).
- **Zero Hardcoded Secrets**: Codebase audits confirm no passwords, private certificates, or Gemini API keys are committed in source files.

---

## 12. Input Validation & SQL Injection Prevention

- **Parameterized ORM Queries**: All database queries use SQLAlchemy ORM expression builders (`.filter()`, `.join()`, `and_()`, `or_()`). No raw SQL string interpolation exists in the project.
- **Strict Pydantic Schemas**: All incoming request bodies are validated with strict Pydantic schemas enforcing data types, string length caps, and enum boundaries.
- **Pagination Capping**: Records pagination query parameters enforce `page >= 1` and `page_size <= 100` (`ge=1, le=100`) to prevent denial-of-service via oversized database queries.

---

## 13. Error Handling & Information Leakage

- **Sanitized Client Errors**: API endpoints catch underlying database or processing errors and return clean, structured JSON messages with appropriate HTTP status codes (`400`, `401`, `403`, `404`, `422`, `429`, `500`).
- **No Traceback Leakage**: Database connection exceptions in health routes do not expose internal PostgreSQL connection strings or passwords.

---

## 14. Logging & Audit Trail

- **Security Alerts Logged**:
  - Failed login attempts and account lockout triggers
  - Password reset requests and token redemptions
  - Email verification completions
  - Active session revocations and permanent account deletions
- **Redacted Information**: Passwords, raw session tokens, password reset tokens, and full raw catalog bodies are **never** logged to server consoles or disk files.

---

## 15. Dependency Security

- **Frontend (`npm audit`)**: **0 Vulnerabilities found** across 1,889 modules.
- **Backend**: Standard dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic`, `openpyxl`, `google-genai`) are pinned with no unmaintained packages.

---

## 16. Production Deployment Requirements

1. **HTTPS Enforcement**: Production ingress (Nginx, Caddy, Cloudflare, or AWS ALB) must terminate TLS and enforce HTTPS across all client traffic.
2. **Cookie Security**: Set `COOKIE_SECURE=true` in the production `.env` environment.
3. **Secret Rotation**: Generate a unique, cryptographically random 64-character string for `AUTH_SECRET`.
4. **PostgreSQL Dedicated User**: Connect using a dedicated PostgreSQL service account with access restricted strictly to the `deadlock` database (no superuser privileges).
5. **Production SMTP Provider**: Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASSWORD` for transactional email delivery (Mailgun, SendGrid, AWS SES).
6. **Distributed Rate Limiting**: Deploy Redis-backed rate limiting if scaling backend services across multiple stateless containers.

---

## 17. Known Limitations

- **Email Delivery in Local Dev**: Defaults to secure console logging rather than sending real emails unless SMTP credentials are provided.
- **Single-Node Rate Limiter**: The current brute-force lockout dictionary is in-memory per worker process; a shared Redis instance is required for multi-pod horizontal scaling.

---

## Final Security Scorecard

| Category | Status | Evidence in Codebase |
| :--- | :--- | :--- |
| **Authentication** | `IMPLEMENTED` | PBKDF2 (100k rounds), brute-force lockout (5 attempts / 300s), case-insensitive email normalization. |
| **Authorization** | `IMPLEMENTED` | Multi-tenant workspace validation across all ingestion, intelligence, enrichment, validation, query, and export endpoints. |
| **IDOR Protection** | `IMPLEMENTED` | Cross-tenant access attempts rejected with `HTTP 403 Forbidden` (`tests/test_data_security.py`). |
| **Password Security** | `IMPLEMENTED` | Minimum 8 chars, 16-byte random salt, single-use SHA-256 hashed reset tokens with 30-min expiry. |
| **Session Security** | `IMPLEMENTED` | Database-tracked `user_sessions`, revocation on logout, automatic session invalidation on password reset. |
| **CORS** | `IMPLEMENTED` | Explicit development origins whitelisted; wildcard `*` removed from `.env`. |
| **CSRF Protection** | `IMPLEMENTED` | `SameSite=Lax` cookie configuration with `Authorization: Bearer` support. |
| **File Upload Security** | `IMPLEMENTED` | Strict `.csv`/`.xlsx` whitelisting, `os.path.basename` path traversal stripping, UUID prefixing, 50MB size limit. |
| **Export Security** | `IMPLEMENTED` | Strict workspace authorization on `/export/{job_id}`, direct binary streaming. |
| **Formula Injection** | `IMPLEMENTED` | Dangerous prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) sanitized with single quote (`'`) in CSV and XLSX exports. |
| **SQL Injection** | `IMPLEMENTED` | 100% parameterized SQLAlchemy ORM expression builders; zero raw SQL string concatenation. |
| **XSS Protection** | `IMPLEMENTED` | React JSX auto-escaping on frontend; `X-XSS-Protection: 1; mode=block` and `X-Content-Type-Options: nosniff` on backend. |
| **Secrets Management** | `IMPLEMENTED` | `.env` gitignored, `.env.example` sanitized, zero secrets in frontend client code or README. |
| **Rate Limiting** | `IMPLEMENTED` | In-memory 5-attempt threshold lockout per email account with 300-second lockout timer. |
| **AI Data Isolation** | `IMPLEMENTED` | Gemini analysis scoped strictly to products within validated `job_id`; API keys held strictly on backend. |
| **Error Handling** | `IMPLEMENTED` | Structured HTTP exceptions with sanitized client messages; zero traceback leakage. |
| **Security Headers** | `IMPLEMENTED` | Middleware injects `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `X-XSS-Protection`. |
| **Dependency Security** | `IMPLEMENTED` | `npm audit` reports 0 vulnerabilities; pinned Python dependencies. |
| **Audit Logging** | `IMPLEMENTED` | Security events logged with token and password redaction. |
| **HTTPS Readiness** | `IMPLEMENTED` | `COOKIE_SECURE` environment toggle and production TLS deployment guide documented. |

---

## Verification Summary

- **Backend Test Suite**: **95 / 95 Tests Passed (100% OK)** in `24.335s` (`python -m unittest discover -s tests`)
- **Frontend Production Build**: **Clean Compile (0 Errors)** in `573ms` (`npm run build`)
