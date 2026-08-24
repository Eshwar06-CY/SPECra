# SPECra — Production Deployment & Operations Guide

> **System**: SPECra Enterprise Product Intelligence Platform  
> **Authors**: Team DEADLOCK (Eshwar M & Granthini CA)  
> **Target Environments**: AWS, GCP, Azure, On-Premises Kubernetes / Docker Engine  
> **Version**: 1.0.0-production

---

## 1. Production Architecture & Network Topology

```
                    INTERNET (Clients & Web Browsers)
                                   │
                                   ▼
                         HTTPS / TLS 1.3 (Port 443)
                                   │
                                   ▼
                    Reverse Proxy / Ingress Layer
                    (Cloudflare / AWS ALB / Nginx)
                    - Ingress TLS Termination
                    - Request Size Limit (50MB)
                    - Edge WAF & Distributed Rate Limiting
                                   │
             ┌─────────────────────┴─────────────────────┐
             │ HTTP (Port 80)                            │ HTTP (Port 8000)
             ▼                                           ▼
      SPECra Web UI                              SPECra Core API
   (React / Vite on Nginx)                     (FastAPI on Uvicorn)
   - Static Asset Caching                     - Tenant Isolation (IDOR)
   - SPA Client-Side Routing                  - CSP & Security Headers
   - Reverse API Proxy                        - Request Validation
                                                         │
                         ┌───────────────────────────────┼───────────────────────────────┐
                         ▼                               ▼                               ▼
               PostgreSQL Data Store             Google Gemini AI                  Brevo SMTP
             - ACID Schema Persistence         - Dedicated Analytics            - Port 587 STARTTLS
             - Encrypted at Rest (AES-256)     - Schema Harmonization           - Verification & Resets
             - 11 Verified RDBMS Tables        - Fallback Determinism           - Zero Token Leakage
```

---

## 2. Infrastructure Prerequisites

| Component | Minimum Specification | Recommended Production Spec |
| :--- | :--- | :--- |
| **Compute (API & UI)** | 2 vCPU, 4 GB RAM | 4 vCPU, 8 GB RAM (or 2+ Load-Balanced Instances) |
| **Database (PostgreSQL)** | PostgreSQL 15+, 2 vCPU, 4 GB RAM | Managed Cloud DB (AWS RDS / GCP Cloud SQL) with Multi-AZ |
| **Disk Storage** | 20 GB SSD (NVMe) | 100 GB SSD with automated snapshot retention |
| **Network** | Public IP with DNS A-Record | HTTPS via valid TLS Certificate (Let's Encrypt / DigiCert) |
| **External Integrations**| Google Gemini API Key | Dedicated GCP Project & Brevo Transactional SMTP Account |

---

## 3. Environment Variables Configuration

Create `/etc/specra/.env` (or load securely from AWS Secrets Manager / GCP Secret Manager / Vault):

```env
# ==============================================================================
# SPECra Core Runtime Configuration
# ==============================================================================
ENVIRONMENT=production
PROJECT_NAME=SPECra
VERSION=1.0.0
API_PREFIX=/api/v1

# Transport Security & CORS
ENABLE_HSTS=true
HSTS_MAX_AGE=31536000
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
CORS_ORIGINS=["https://app.specra.io"]
FRONTEND_BASE_URL=https://app.specra.io
MAX_REQUEST_BODY_SIZE_MB=50

# Security & Master Auth Secret (Must be 32+ characters of random entropy)
AUTH_SECRET=4f9b2d8e7a1c503698f2e4b7c1d3a5e8246813579bdf02468ace13579bdf0246
SESSION_EXPIRE_HOURS=168
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_SECONDS=300
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30

# PostgreSQL Production Connection
DATABASE_URL=postgresql://specra_app:SECURE_DB_PASSWORD@postgres.internal:5432/deadlock?sslmode=require

# Google Gemini AI Dedicated Engine
GEMINI_API_KEY=AIzaSy...YOUR_GCP_GEMINI_KEY
GEMINI_MODEL=gemini-3.7-flash
GEMINI_MAX_CONCURRENCY=5
GEMINI_REQUEST_TIMEOUT=30.0
GEMINI_MAX_RETRIES=3

# Brevo Transactional Email Delivery (Port 587 STARTTLS)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=7a8b9c@smtp-brevo.com
SMTP_PASSWORD=xsmtpsib-SECURE_BREVO_KEY
SMTP_FROM_EMAIL=no-reply@specra.io
SMTP_FROM_NAME=SPECra Product Intelligence
SMTP_USE_TLS=true

# Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=50
```

---

## 4. PostgreSQL Database Hardening

### Step 4.1: Create Dedicated Least-Privilege Application User

Connect as PostgreSQL superuser (`postgres`) and execute:

```sql
-- 1. Create database
CREATE DATABASE deadlock WITH OWNER postgres ENCODING 'UTF8';

-- 2. Create dedicated non-superuser application role
CREATE USER specra_app WITH PASSWORD 'SECURE_APPLICATION_DB_PASSWORD';

-- 3. Connect to database
\c deadlock

-- 4. Grant required DML permissions on public schema
GRANT CONNECT ON DATABASE deadlock TO specra_app;
GRANT USAGE ON SCHEMA public TO specra_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO specra_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO specra_app;

-- 5. Ensure future tables maintain least-privilege permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO specra_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO specra_app;
```

### Step 4.2: Initialize and Migrate Schema

Run database initialization and migration:

```powershell
python backend/scripts/init_db.py
```

---

## 5. Reverse Proxy Configuration (Nginx Ingress)

Create `/etc/nginx/sites-available/specra.conf`:

```nginx
# Upstream Backend Pool
upstream specra_api_cluster {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

# HTTP -> HTTPS Redirect
server {
    listen 80;
    listen [::]:80;
    server_name app.specra.io api.specra.io;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.specra.io;

    # TLS Certificates
    ssl_certificate /etc/letsencrypt/live/app.specra.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.specra.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Ingress Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Static Web UI Assets
    root /var/www/specra/frontend/dist;
    index index.html;

    client_max_body_size 50M;

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml image/svg+xml;

    # API Proxy to FastAPI Core
    location /api/ {
        proxy_pass http://specra_api_cluster;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # Health Probes
    location /health {
        proxy_pass http://specra_api_cluster/health;
        access_log off;
    }

    location /ready {
        proxy_pass http://specra_api_cluster/ready;
        access_log off;
    }

    # SPA Routing Fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 6. Systemd Production Service Setup

Create `/etc/systemd/system/specra-api.service`:

```ini
[Unit]
Description=SPECra FastAPI Application Service
After=network.target postgresql.service

[Service]
Type=simple
User=specra
Group=specra
WorkingDirectory=/var/www/specra/backend
EnvironmentFile=/etc/specra/.env
ExecStart=/var/www/specra/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --proxy-headers
Restart=always
RestartSec=5s
LimitNOFILE=65536

# Sandbox Hardening
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable specra-api
sudo systemctl start specra-api
sudo systemctl status specra-api
```

---

## 7. Containerized Deployment (Docker Compose)

Deploy using the verified production compose specification:

```bash
# 1. Clone repository
git clone <repository-url> specra-production
cd specra-production

# 2. Configure production .env
cp backend/.env.example .env
# Edit .env with production credentials

# 3. Build and launch container stack
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify running container health
docker compose -f docker-compose.prod.yml ps
```

---

## 8. Health Probes & Operational Monitoring

| Endpoint | Probe Type | Expected HTTP Status | Validation Purpose |
| :--- | :--- | :---: | :--- |
| `GET /health` | Liveness | `HTTP 200` | Verifies ASGI web worker availability. |
| `GET /ready` | Readiness | `HTTP 200` | Verifies active PostgreSQL database connectivity. |

---

## 9. Backup & Disaster Recovery Procedures

### Daily Automated PostgreSQL Snapshot Script (`/usr/local/bin/backup-specra-db.sh`):

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/specra"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/specra_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

# Execute compressed PostgreSQL dump
pg_dump -h localhost -U specra_app -d deadlock | gzip > "${BACKUP_FILE}"

# Encrypt backup archive with GPG
gpg --symmetric --batch --passphrase-file /etc/specra/backup_key.txt "${BACKUP_FILE}"
rm "${BACKUP_FILE}"

# Enforce 30-day retention policy
find "${BACKUP_DIR}" -name "*.sql.gz.gpg" -type f -mtime +30 -delete

echo "SPECra database backup completed successfully at ${TIMESTAMP}."
```

### Database Restore Procedure:

```bash
# 1. Decrypt archive
gpg --decrypt --batch --passphrase-file /etc/specra/backup_key.txt specra_backup_YYYYMMDD.sql.gz.gpg > restore.sql.gz

# 2. Restore into target database
gunzip -c restore.sql.gz | psql -h localhost -U specra_app -d deadlock
```
