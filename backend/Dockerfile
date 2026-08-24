# ==============================================================================
# SPECra Backend Production Dockerfile
# Multi-Stage Build with Non-Root Security Hardening
# ==============================================================================

# --- Stage 1: Build Stage ---
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim as runtime

# Create isolated non-root user and group
RUN groupadd -g 1001 specra && \
    useradd -u 1001 -g specra -s /bin/bash -m specra

WORKDIR /app

# Install runtime PostgreSQL client library and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder stage
COPY --from=builder --chown=specra:specra /root/.local /home/specra/.local
ENV PATH=/home/specra/.local/bin:$PATH

# Copy application source code
COPY --chown=specra:specra app/ ./app
COPY --chown=specra:specra scripts/ ./scripts

# Create and set permissions for uploads directory
RUN mkdir -p /app/uploads && chown -R specra:specra /app/uploads

# Switch to non-root user
USER specra

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
