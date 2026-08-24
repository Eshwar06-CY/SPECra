# SPECra

> **AI-Powered Product Intelligence for Industrial Commerce**

Turn messy, incomplete, and heterogeneous industrial product spreadsheets into standardized, enriched, evidence-backed, and commerce-ready product catalogs.

---

### Team Information
- **Product Name**: SPECra
- **Development Team**: Team DEADLOCK
- **Team Members**: 
  - Eshwar M
  - Granthini CA
- **Institution**: Vidyavardhaka College of Engineering (VVCE)
- **Competition Track**: UniHack 2026

---

## 1. Project Overview

Industrial distributors, manufacturers, and B2B commerce platforms struggle with messy, unstandardized product catalogs. Supplier data arrives across hundreds of fragmented spreadsheets with:
- **Inconsistent product naming** (abbreviations, mixed brand/series names, missing product classes).
- **Embedded physical dimensions** tangled inside unstructured descriptions (e.g. `1/2"x18"` or `1-1/2 in`).
- **Ambiguous packaging units** (e.g. `6pc`, `50/Box`, `100/Pack`, `Carton of 12`).
- **Missing or conflicting identity fields** (misplaced MPNs, missing brand tags, unclear manufacturers).
- **Complete lack of traceable evidence** (hallucinated numbers with no audit trail back to raw source cells).

### The SPECra Solution
SPECra provides an intelligent end-to-end data refinery. Users upload any industrial CSV or Excel catalog, state what specifications they require in natural language, and SPECra automatically:
1. Detects schemas and infers column semantics dynamically.
2. Extracts canonical product identity, specifications, and features using Google Gemini AI.
3. Deterministically normalizes units, physical dimensions, fractions, and packaging quantities.
4. Anchors every extracted and derived attribute to raw source text with traceable provenance.
5. Performs a multi-point quality and physical consistency validation audit.
6. Delivers standardized datasets in CSV, Excel, or the comprehensive **252-column UniHack-compliant schema**.

---

## 2. How SPECra Works

SPECra uses a **Hybrid Architecture** combining generative AI with deterministic normalization:
- **AI Intelligence Layer**: Interprets ambiguous unstructured product descriptions, identifies product categories, and extracts qualitative features.
- **Deterministic Rules Engine**: Handles fraction-to-decimal conversions, unit standardization, brand reconciliation, packaging logic, evidence anchoring, and 252-column mapping.

```mermaid
flowchart TD
    User([User]) --> Login[1. Secure Authentication]
    Login --> Ingest[2. CSV / XLSX Ingestion]
    Ingest --> Schema[3. Dynamic Schema Inference]
    Schema --> Req[4. Natural Language Requirements]
    Req --> AI[5. AI Product Intelligence Engine]
    AI --> Enrich[6. Deterministic Enrichment & Normalization]
    Enrich --> Evidence[7. Evidence & Provenance Anchoring]
    Evidence --> Validate[8. Physical Validation & Quality Audit]
    Validate --> Review[9. Smart Search & Product Inspection]
    Review --> Export[10. UniHack 252-Column & Custom Export]
```

### No-Hallucination Philosophy
If a product catalog row does not contain or imply a required specification, SPECra **leaves the field blank**. The platform never hallucinates synthetic specifications or fabricates measurements.

---

## 3. Key Features

| Feature | What It Does | Why It Matters | User Benefit |
| :--- | :--- | :--- | :--- |
| **Server-Side Auth & Isolation** | PBKDF2 password hashing with isolated workspaces and HttpOnly session cookies. | Keeps enterprise catalog data private and separated between tenant accounts. | User A can never view, query, or export User B's catalog data. |
| **Universal Catalog Ingestion** | Ingests CSV and Excel files up to 50MB with flexible UTF encoding and delimiter handling. | No need to reformat source supplier spreadsheets prior to upload. | Instant catalog onboarding without rigid manual mapping templates. |
| **Dynamic Schema Inference** | Analyzes column data types, completeness, null ratios, and semantic roles (MPN, name, brand). | Understands incoming data structures without pre-configured schemas. | Immediate insight into catalog health and populated columns. |
| **Natural-Language Querying** | Converts plain English requirements (e.g., *"Find 3M sanding discs with diameter and pack qty"*) into SQL execution plans. | Users don't need SQL or database expertise to query and filter data. | Intuitive query workflow with instant preview and explainability. |
| **AI Product Intelligence** | Uses Google Gemini (`gemini-3.7-flash`) with structured JSON schema constraints. | Extracts canonical product titles, manufacturers, brands, MPNs, and specifications. | Unstructured descriptions turn into structured, queryable data. |
| **Deterministic Normalization** | Converts fractions (`1/2"` &rarr; `0.5 in`), standardizes UOMs, and resolves packaging (`6pc` &rarr; `6 pieces`). | Eliminates human data-cleaning errors and inconsistent unit representations. | Consistent, machine-readable specifications ready for ERP/PIM systems. |
| **Traceable Evidence & Badges** | Anchors attributes to source text; marks fields as `DIRECT` or `DERIVED`. | Full auditability for every single attribute extracted. | Reviewers see exact source quotes and transformation reasons. |
| **Validation & Quality Scoring** | Evaluates identity completeness, dimensional sanity, unit validity, and attribute consistency. | Flags errors and warnings before catalog data is exported to commerce systems. | 0–100 quality score showing catalog reliability at a glance. |
| **252-Column UniHack Export** | Generates compliant CSV or XLSX files mapping to all 252 official UniHack specification headers. | Conforms strictly to enterprise commerce and competition standards. | One-click delivery of fully compliant, standardized catalog files. |

---

## 4. System Architecture

```mermaid
graph TB
    subgraph Frontend ["Frontend Layer (React 19 + TypeScript + Vite)"]
        UI[SPECra SaaS UI & Design System]
        AuthContext[Auth & Session Manager]
        QueryUI[Ask Your Catalog & Table View]
        Drawer[Evidence & Product Drawer]
    end

    subgraph Backend ["Backend API Layer (FastAPI + Python 3.13)"]
        AuthRouter["/api/v1/auth"]
        IngestRouter["/api/v1/ingestion"]
        IntelRouter["/api/v1/intelligence"]
        EnrichRouter["/api/v1/enrichment"]
        ValRouter["/api/v1/validation"]
        QueryRouter["/api/v1/query"]
        ExportRouter["/api/v1/export"]
    end

    subgraph CoreServices ["Core Services & Processing Engines"]
        AuthService[Auth & Workspace Service]
        IngestService[Ingestion & Pandas Parser]
        IntelService[AI Intelligence Service]
        EnrichEngine[Deterministic Normalizer]
        ValEngine[Quality & Validation Auditor]
        QueryPlanner[Natural Language Query Planner]
        ExportEngine[252-Column UniHack Mapper]
    end

    subgraph StorageAI ["Data & AI Provider"]
        PG[(PostgreSQL Database)]
        Gemini[Google Gemini API gemini-3.7-flash]
    end

    UI --> Backend
    Backend --> CoreServices
    CoreServices --> PG
    IntelService --> Gemini
    QueryPlanner --> Gemini
```

---

## 5. End-to-End Data Transformation Example

### Raw Supplier Row:
```json
{
  "Mfg_Part_Num": "DCB518ASTS06G",
  "Part_Desc": "DCB518ASTS06G Diablo 1/2\"x18\" - Sanding Belt 6pc",
  "Part_Manuf": "Freud Inc (2435)"
}
```

### SPECra Transformation:
| Field | Value | Unit | Provenance | Source Anchor | Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Product Name** | `Diablo 1/2" x 18" Sanding Belt, 6-Pack` | — | `DERIVED` | `Part_Desc` | AI + Normalization |
| **MANUFACTURER_PART_NUMBER** | `DCB518ASTS06G` | — | `DIRECT` | `Mfg_Part_Num` | Deterministic |
| **MANUFACTURER_NAME** | `Freud Inc (2435)` | — | `DIRECT` | `Part_Manuf` | Deterministic |
| **BRAND_NAME** | `Diablo` | — | `DIRECT` | `Part_Desc` | Reconciled Identity |
| **WIDTH** | `0.5` | `in` | `DERIVED` | `1/2"x18"` | Fraction Normalization |
| **LENGTH** | `18` | `in` | `DERIVED` | `1/2"x18"` | Unit Standardization |
| **Selling Qty** | `6` | — | `DERIVED` | `6pc` | Packaging Extraction |
| **Selling UOM** | `pieces` | — | `DERIVED` | `6pc` | Packaging Semantics |
| **Class** | `Sanding Belt` | — | `DIRECT` | `Part_Desc` | Taxonomy Mapping |

---

## 6. Project Directory Structure

```
deadlock/
├── backend/
│   ├── app/
│   │   ├── ai/               # Gemini client & natural-language query planner
│   │   ├── api/              # FastAPI routers (auth, ingestion, intelligence, etc.)
│   │   ├── core/             # Config, database engine, security utilities
│   │   ├── models/           # SQLAlchemy ORM models (user, workspace, product, etc.)
│   │   ├── schemas/          # Pydantic validation models & API contracts
│   │   ├── services/         # Business logic (ingestion, enrichment, export, etc.)
│   │   └── main.py           # Application entrypoint & middleware configuration
│   ├── tests/                # Automated test suite (77 tests, 100% passing)
│   ├── .env.example          # Environment variables template
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios client with interceptors
│   │   ├── assets/           # SPECra SVG brand logo and marks
│   │   ├── components/       # UI components (sidebar, topbar, drawers, logo)
│   │   ├── context/          # AppContext and AuthContext
│   │   ├── pages/            # Landing, Login, Dashboard, Upload, Results, etc.
│   │   └── types/            # TypeScript interfaces for API contracts
│   ├── package.json          # Node dependencies & build scripts
│   └── vite.config.ts        # Vite build configuration
├── submission/               # Generated UniHack demo videos & submission assets
├── README.md                 # Technical documentation
└── USER_MANUAL.md            # Non-technical end-user guide
```

---

## 7. API Reference

| Domain | Method | Endpoint | Purpose |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new user account and provision default workspace |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate credentials, reset rate limiting, issue fresh session |
| **Auth** | `GET` | `/api/v1/auth/me` | Retrieve authenticated user profile and workspace info |
| **Auth** | `POST` | `/api/v1/auth/logout` | Revoke active server-side session |
| **Auth** | `POST` | `/api/v1/auth/forgot-password` | Request single-use hashed password reset token via email |
| **Auth** | `POST` | `/api/v1/auth/reset-password` | Reset password using valid token and invalidate prior sessions |
| **Auth** | `POST` | `/api/v1/auth/change-password` | Update passphrase and revoke other active login sessions |
| **Auth** | `GET` | `/api/v1/auth/verify-email` | Verify account email address with single-use token |
| **Auth** | `GET` | `/api/v1/auth/sessions` | Inspect active login sessions for authenticated user |
| **Auth** | `DELETE` | `/api/v1/auth/sessions/{id}` | Revoke specific active session |
| **Auth** | `POST` | `/api/v1/auth/delete-account` | Permanently delete account and cascading workspace data |
| **Ingestion** | `POST` | `/api/v1/ingestion/upload` | Upload CSV/XLSX catalog file and trigger schema analysis |
| **Ingestion** | `GET` | `/api/v1/ingestion/jobs` | List processing jobs belonging to authenticated workspace |
| **Ingestion** | `GET` | `/api/v1/ingestion/{job_id}` | Retrieve job processing status and statistics |
| **Ingestion** | `GET` | `/api/v1/ingestion/{job_id}/records` | Paginated product records from uploaded catalog |
| **Intelligence** | `POST` | `/api/v1/intelligence/analyze/{job_id}` | Run AI product intelligence extraction over catalog records |
| **Intelligence** | `GET` | `/api/v1/intelligence/product/{id}` | Detailed product attributes, features, and source evidence |
| **Enrichment** | `POST` | `/api/v1/enrichment/product/{id}` | Execute deterministic unit normalization & enrichment |
| **Enrichment** | `GET` | `/api/v1/enrichment/product/{id}` | Retrieve stored enrichment report and field provenance |
| **Validation** | `POST` | `/api/v1/validation/product/{id}` | Execute physical validation and quality audit |
| **Validation** | `GET` | `/api/v1/validation/product/{id}` | Retrieve quality audit findings, scores, and severity |
| **Query** | `POST` | `/api/v1/query/{job_id}/preview` | Preview natural-language query interpretation |
| **Query** | `POST` | `/api/v1/query/{job_id}` | Execute structured catalog search against PostgreSQL |
| **Export** | `GET` | `/api/v1/export/{job_id}/preview` | Preview mapped 252-column export dataset and fill rates |
| **Export** | `POST` | `/api/v1/export/{job_id}?format=csv` | Generate and download 252-column UniHack CSV export |
| **Export** | `POST` | `/api/v1/export/{job_id}?format=xlsx` | Generate and download 252-column UniHack Excel export |

---

## 8. Installation & Setup

### Prerequisites
- **OS**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.11 or higher (3.13 recommended)
- **Node.js**: Version 18 or higher (with npm)
- **PostgreSQL**: Version 14 or higher running locally or in Docker

### Step 1: Clone Repository
```powershell
git clone https://github.com/Eshwar06-CY/deadlock.git
cd deadlock
```

### Step 2: Backend Setup
```powershell
# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
```

Edit `backend/.env` with your credentials:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/deadlock
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.7-flash
AUTH_SECRET=your_32_character_secret_key_here
```

### Step 3: Frontend Setup
```powershell
cd ..\frontend
npm install
```

---

## 9. Running the Application

### Start Backend Server
```powershell
cd D:\Antigravity_Projects\deadlock\backend
..\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```
- **Backend API**: `http://127.0.0.1:8001`
- **Interactive Swagger Docs**: `http://127.0.0.1:8001/docs`

### Start Frontend Application
```powershell
cd D:\Antigravity_Projects\deadlock\frontend
npm run dev
```
- **Web Application**: `http://localhost:5173`

---

## 10. Automated Testing

### Backend Test Suite (171 Tests)
```powershell
cd D:\Antigravity_Projects\deadlock\backend
..\venv\Scripts\Activate.ps1
python -m unittest discover -s tests
```
*Executes unit tests, database integrations, Gemini AI abstractions, deterministic enrichment rules, multi-tenant IDOR security checks, password resets with single-use tokens, session management, cryptographic email verification, Brevo/SMTP email dispatch abstractions, path traversal defenses, spreadsheet formula injection sanitization, HTTP security headers (CSP, HSTS, X-Frame-Options), request size protection, adversarial red-team test validations, readiness probes, production startup validation, natural-language query planning, and 252-column export verifications.*

### Frontend Production Build
```powershell
cd D:\Antigravity_Projects\deadlock\frontend
npm run build
```
*Compiles TypeScript and bundles production assets via Vite.*

---

## 11. Security & Email Architecture

### Implemented Security Measures
- **Password Security**: PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user 16-byte random salt.
- **Cryptographic Token Lifecycle**: 256-bit CSPRNG tokens (`secrets.token_urlsafe(32)`) with single-use SHA-256 hash storage and expiration enforcement.
- **Email Verification & Password Reset**: Automated workflows with global session revocation upon password reset and generic anti-enumeration responses.
- **Transactional Brevo SMTP Delivery**: Integrated Brevo SMTP (Port 587 STARTTLS) with zero token/credential leakage in logs or responses.
- **Session Protection**: Server-side session tokens stored in PostgreSQL with HttpOnly/SameSite cookie and Bearer header fallback.
- **Multi-Tenant Isolation (IDOR Defense)**: Resources (datasets, products, intelligence, enrichments, validations, natural-language queries, exports) strictly bound to `workspace_id` with verified `403 Forbidden` rejection.
- **HTTP Security Headers**: Enterprise middleware enforcing `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, strict Content Security Policy (CSP), and configurable HSTS.
- **Request Size & Upload Protection**: 50MB global request body capping (`HTTP 413`), sanitized filenames, and UUID-isolated storage.
- **Spreadsheet Formula Injection Defense**: Neutralizes executable spreadsheet cells starting with `=`, `@`, `+`, or `\t` during CSV and XLSX generation.
- **SQL Injection Prevention**: Safe parameterized queries via SQLAlchemy ORM and schema whitelisting.
- **CORS Whitelisting**: Restricted to explicitly approved development origins (`localhost:5173`, `localhost:3000`).

### Production Deployment Hardening
- Enforce ingress TLS 1.3 termination on reverse proxy (Cloudflare / AWS ALB / Nginx).
- Configure dedicated least-privilege PostgreSQL application user (`SELECT, INSERT, UPDATE, DELETE` only).
- Deploy Redis cluster for distributed multi-instance rate limiting.
- Enable automated encrypted cloud database snapshots and point-in-time recovery (PITR).
- Store master production secrets in cloud secret vaults (e.g. AWS Secrets Manager, GCP Secret Manager).

---

## 12. Troubleshooting

| Issue | Likely Cause | Solution |
| :--- | :--- | :--- |
| **Backend connection refused (10061)** | Backend server is not running or crashed on startup. | Run `uvicorn app.main:app --reload --port 8001` in `backend/` directory. |
| **Database connection error** | PostgreSQL is not running or `DATABASE_URL` is misconfigured. | Ensure PostgreSQL service is active on port 5432 and database `deadlock` exists. |
| **AI processing timeout / 503** | Upstream Gemini API rate limit or transient network latency. | Verify `GEMINI_API_KEY` in `.env`. System will automatically apply exponential retries. |
| **CORS error in browser console** | Origin mismatch between frontend and backend. | Verify frontend URL is listed in `CORS_ORIGINS` in `backend/app/core/config.py`. |
| **Port 8001 or 5173 already in use** | An existing background server process is still bound to the port. | Terminate the occupying PID using PowerShell (`Get-Process`) or choose an alternate port. |

---

## 13. Limitations & Future Roadmap

### Current Limitations
- AI extraction rate is subject to Gemini API quota limits.
- Background asynchronous worker queues (Celery/Redis) are planned for datasets exceeding 10,000 rows.

### Future Roadmap
- **PDF & Spec Sheet OCR**: Direct extraction from industrial PDF spec sheets, technical drawings, and brochures.
- **Vision-Language Analysis**: Visual inspection of product CAD drawings and packaging photography.
- **Automated ERP Connectors**: Direct sync adapters for SAP, Shopify Plus, Akeneo PIM, and BigCommerce.
