import logging
import uuid
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.database import router as database_router
from app.api.ingestion import router as ingestion_router
from app.api.intelligence import router as intelligence_router
from app.api.validation import router as validation_router
from app.api.export import router as export_router
from app.api.enrichment import router as enrichment_router
from app.api.query import router as query_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# Enable CORS with strict origins whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_size_middleware(request: Request, call_next):
    """
    Applies enterprise security headers and enforces maximum request body size limits.
    """
    # 1. Enforce Request Size Limit
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length_bytes = int(content_length)
            max_bytes = settings.MAX_REQUEST_BODY_SIZE_MB * 1024 * 1024
            if length_bytes > max_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request entity too large. Maximum permitted size is {settings.MAX_REQUEST_BODY_SIZE_MB}MB."},
                )
        except ValueError:
            pass

    # 2. Process Request
    response = await call_next(request)

    # 3. Inject Enterprise Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=(), usb=(), display-capture=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # CSP designed specifically for React/Vite SPECra UI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' http: https: ws: wss:; "
        "frame-ancestors 'none';"
    )

    # Conditional HSTS (Strict-Transport-Security) - Enabled in production or when explicitly configured
    if settings.ENABLE_HSTS or settings.ENVIRONMENT.lower() == "production":
        hsts_val = f"max-age={settings.HSTS_MAX_AGE}"
        if settings.HSTS_INCLUDE_SUBDOMAINS:
            hsts_val += "; includeSubDomains"
        if settings.HSTS_PRELOAD:
            hsts_val += "; preload"
        response.headers["Strict-Transport-Security"] = hsts_val

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Sanitizes unhandled exceptions in production to prevent stack trace or credential leakage.
    """
    error_id = uuid.uuid4().hex[:12]
    logger.exception(f"Unhandled Exception [Error ID: {error_id}] on {request.method} {request.url.path}: {exc}")

    if settings.ENVIRONMENT.lower() == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected internal server error occurred. Please contact support if the issue persists.",
                "error_id": error_id,
            },
        )

    # In development/test mode, return standard error detail for debugging
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "error_id": error_id},
    )

# Register API routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(database_router, prefix=settings.API_PREFIX)
app.include_router(ingestion_router, prefix=settings.API_PREFIX)
app.include_router(intelligence_router, prefix=settings.API_PREFIX)
app.include_router(validation_router, prefix=settings.API_PREFIX)
app.include_router(export_router, prefix=settings.API_PREFIX)
app.include_router(enrichment_router, prefix=settings.API_PREFIX)
app.include_router(query_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "project": "Deadlock",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe for container orchestrators and load balancers.
    Verifies database connectivity without leaking internal metadata.
    """
    from app.core.database import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1;"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        logger.error(f"Readiness probe failed: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "detail": "Database service unavailable."},
        )
